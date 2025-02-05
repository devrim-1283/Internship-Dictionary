# Backup Uygulaması Kurulum Kılavuzu

## Gereksinimler

Kurulum yapmadan önce aşağıdaki yazılımların bilgisayarınızda yüklü olduğundan emin olun:

1. Python 3.8 veya daha yüksek bir sürüm
   - [Python'u buradan indirebilirsiniz](https://www.python.org/downloads/)
   - Kurulum sırasında "Add Python to PATH" seçeneğini işaretlemeyi unutmayın

2. Gerekli Python paketleri:
   ```bash
   pip install pyinstaller
   pip install pywin32
   ```

## Kurulum Adımları

1. Dosyaları bilgisayarınıza indirin
   - `installer.py`
   - `main.py`
   - `icon_backup.ico` (isteğe bağlı)
   - Tüm dosyaların aynı klasörde olduğundan emin olun

2. Kurulumu başlatın
   - `installer.py` dosyasına sağ tıklayın
   - "Yönetici olarak çalıştır" seçeneğini seçin
   - Veya komut istemini yönetici olarak açıp şu komutu çalıştırın:
     ```bash
     python installer.py
     ```

3. Kurulum sihirbazını takip edin
   - Varsayılan yedekleme şifresini girin
   - USB sürücüler için anahtar şifresini belirleyin
   - Windows başlangıcında otomatik başlatma seçeneğini belirleyin

## Kurulum Sonrası

Kurulum tamamlandığında:
- Program `%APPDATA%\BackupApp` klasörüne kurulacak
- Masaüstünde ve Başlat menüsünde kısayollar oluşturulacak
- USB sürücüler için `.key` dosyası İndirilenler klasörünüze kaydedilecek

## Sorun Giderme

1. "Administrator rights required" hatası alırsanız:
   - Programı yönetici olarak çalıştırdığınızdan emin olun

2. PyInstaller hataları için:
   - Python'un PATH'e eklendiğinden emin olun
   - Gerekli paketlerin doğru şekilde yüklendiğini kontrol edin

3. Kurulum sırasında hata alırsanız:
   - Tüm dosyaların aynı klasörde olduğunu kontrol edin
   - Antivirüs programınızın kurulumu engellemediğinden emin olun
   - Eski kurulumu kaldırıp tekrar deneyin

## İletişim

Herhangi bir sorun yaşarsanız veya yardıma ihtiyacınız olursa:
[İletişim bilgilerinizi buraya ekleyin]

## Lisans

[Lisans bilgilerinizi buraya ekleyin] 