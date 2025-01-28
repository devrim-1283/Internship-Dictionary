import os
import sys
import shutil
import ctypes
from win32com.client import Dispatch
import winreg
import subprocess
import json

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def create_shortcut(target_path, shortcut_path, working_dir):
    """Windows kısayolu oluşturur"""
    try:
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = target_path
        shortcut.WorkingDirectory = working_dir
        shortcut.save()
        return True
    except Exception as e:
        print(f"Kısayol oluşturma hatası: {str(e)}")
        return False

def add_to_startup(exe_path):
    """Programı Windows başlangıcına ekler"""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, 'BackupApp', 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"Başlangıca ekleme hatası: {str(e)}")
        return False

def create_key_file(key_content):
    """USB bellekler için .key dosyası oluşturur"""
    try:
        downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads')
        key_path = os.path.join(downloads_path, '.key')
        
        with open(key_path, 'w') as f:
            f.write(key_content)
        
        print(f"\n.key dosyası oluşturuldu: {key_path}")
        print("Bu dosyayı USB belleğinize kopyalayarak yedekleme yapabilirsiniz.")
        return True
    except Exception as e:
        print(f".key dosyası oluşturulurken hata: {str(e)}")
        return False

def create_config(default_password):
    """Config dosyasını oluşturur"""
    try:
        config = {
            "default_password": default_password
        }
        
        config_dir = os.path.join(os.getcwd(), 'config')
        os.makedirs(config_dir, exist_ok=True)
        
        config_path = os.path.join(config_dir, 'backup_config.json')
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        
        return True
    except Exception as e:
        print(f"Config dosyası oluşturulurken hata: {str(e)}")
        return False

def compile_and_install():
    try:
        current_dir = os.getcwd()
        
        # Gerekli dosyaları kontrol et
        if not os.path.exists('main.py'):
            print("Hata: main.py dosyası bulunamadı!")
            print("Lütfen installer.py'yi main.py ile aynı klasöre koyun.")
            return False
        
        # Kullanıcıdan bilgileri al
        print("\nKurulum için gerekli bilgileri giriniz:")
        print("-" * 40)
        
        # Varsayılan şifre
        default_password = input("Varsayılan yedekleme şifresi: ")
        if not default_password:
            print("Şifre boş olamaz!")
            return False
            
        # USB key şifresi
        key_content = input("USB bellekler için anahtar şifresi: ")
        if not key_content:
            print("Anahtar şifresi boş olamaz!")
            return False
        
        # Config klasörünü oluştur ve config dosyasını oluştur
        print("\nConfig dosyası oluşturuluyor...")
        if not create_config(default_password):
            return False
            
        # .key dosyasını oluştur
        print("\nKey dosyası oluşturuluyor...")
        if not create_key_file(key_content):
            return False
        
        # PyInstaller ile exe oluştur
        print("\nProgram derleniyor...")
        try:
            # Eski build ve dist klasörlerini temizle
            for folder in ['build', 'dist']:
                if os.path.exists(folder):
                    shutil.rmtree(folder)
            
            # Python yolunu al
            python_exe = sys.executable
            
            # Icon kontrolü
            icon_path = os.path.join(current_dir, 'icon_backup.ico')
            if not os.path.exists(icon_path):
                print("Uyarı: icon_backup.ico bulunamadı. Varsayılan ikon kullanılacak.")
                command = f'"{python_exe}" -m PyInstaller --noconfirm --onefile --windowed --add-data "config;config" main.py'
            else:
                command = f'"{python_exe}" -m PyInstaller --noconfirm --onefile --windowed --icon="{icon_path}" --add-data "config;config" main.py'
            
            # PyInstaller'ı çalıştır
            print("Derleme komutu çalıştırılıyor...")
            print(f"Komut: {command}")
            
            result = subprocess.run(
                command,
                shell=True,
                cwd=current_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print("PyInstaller hatası:")
                print(result.stderr)
                return False
                
            print("Program başarıyla derlendi!")
            
        except Exception as e:
            print(f"Derleme hatası: {str(e)}")
            print("Hata detayı:")
            import traceback
            traceback.print_exc()
            return False
            
        # Exe dosyasının oluşturulduğunu kontrol et
        source_exe = os.path.join(current_dir, 'dist', 'main.exe')
        if not os.path.exists(source_exe):
            print(f"Hata: Exe dosyası oluşturulamadı: {source_exe}")
            print("PyInstaller çıktısı:")
            print(result.stdout)
            print("\nPyInstaller hata çıktısı:")
            print(result.stderr)
            return False
        
        # Kurulum klasörünü belirle
        install_dir = os.path.join(os.getenv('APPDATA'), 'BackupApp')
        
        # Eski kurulumu temizle
        if os.path.exists(install_dir):
            try:
                shutil.rmtree(install_dir)
            except Exception as e:
                print(f"Eski kurulum kaldırılamadı: {str(e)}")
                print("Lütfen programı kapatıp tekrar deneyin.")
                return False
        
        # Kurulum klasörünü oluştur
        os.makedirs(install_dir, exist_ok=True)
        
        # Exe dosyasını kopyala
        target_exe = os.path.join(install_dir, 'backup.exe')
        
        try:
            shutil.copy2(source_exe, target_exe)
            print("Program dosyası kopyalandı")
        except Exception as e:
            print(f"Exe kopyalama hatası: {str(e)}")
            return False
        
        # Config klasörünü kopyala
        config_dir = os.path.join(current_dir, 'config')
        if os.path.exists(config_dir):
            try:
                if os.path.exists(os.path.join(install_dir, 'config')):
                    shutil.rmtree(os.path.join(install_dir, 'config'))
                shutil.copytree(config_dir, os.path.join(install_dir, 'config'))
                print("Config dosyaları kopyalandı")
            except Exception as e:
                print(f"Config kopyalama hatası: {str(e)}")
                return False
        
        # Kısayolları oluştur
        start_menu_dir = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs')
        shortcut_path = os.path.join(start_menu_dir, 'Backup App.lnk')
        
        if create_shortcut(target_exe, shortcut_path, install_dir):
            print("Başlat menüsü kısayolu oluşturuldu")
        
        desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        desktop_shortcut = os.path.join(desktop_path, 'Backup App.lnk')
        
        if create_shortcut(target_exe, desktop_shortcut, install_dir):
            print("Masaüstü kısayolu oluşturuldu")
        
        # Windows başlangıcına ekleme seçeneği
        startup_choice = input("\nProgram Windows ile birlikte başlatılsın mı? (E/H): ")
        if startup_choice.lower() == 'e':
            if add_to_startup(target_exe):
                print("Program başlangıca eklendi")
        
        print("\nKurulum başarıyla tamamlandı!")
        print(f"Program şu konuma kuruldu: {install_dir}")
        
        # Programı başlatma seçeneği
        run_now = input("\nProgram şimdi çalıştırılsın mı? (E/H): ")
        if run_now.lower() == 'e':
            os.startfile(target_exe)
        
        return True
        
    except Exception as e:
        print(f"\nKurulum sırasında hata oluştu: {str(e)}")
        return False

def main():
    print("Backup App Kurulum Sihirbazı")
    print("-" * 30)
    
    # Yönetici izni kontrolü
    if not is_admin():
        print("Kurulum için yönetici izni gerekiyor...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        return
    
    # Kullanıcı onayı
    print("\nBu program şunları yapacak:")
    print("1. Programı derleyip exe dosyası oluşturacak")
    print("2. Programı AppData klasörüne kuracak")
    print("3. Başlat menüsüne ve masaüstüne kısayol ekleyecek")
    print("4. USB bellekler için .key dosyası oluşturacak")
    print("5. İsteğe bağlı olarak Windows başlangıcına ekleyecek")
    
    choice = input("\nKuruluma devam etmek istiyor musunuz? (E/H): ")
    if choice.lower() != 'e':
        print("\nKurulum iptal edildi.")
        input("Çıkmak için bir tuşa basın...")
        return
    
    print("\nKurulum başlatılıyor...")
    if compile_and_install():
        print("\nKurulum tamamlandı!")
    else:
        print("\nKurulum başarısız oldu!")
    
    input("\nÇıkmak için bir tuşa basın...")

if __name__ == "__main__":
    main() 