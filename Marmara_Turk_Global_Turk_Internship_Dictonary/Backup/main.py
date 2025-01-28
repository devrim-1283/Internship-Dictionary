import sys
import psutil
import os
import platform
import logging
from datetime import datetime
from PyQt5 import QtWidgets, QtCore, QtGui
from backup_ui import Ui_Form
from PyQt5.QtCore import QThread, pyqtSignal
import shutil
from zipfile import ZipFile, ZIP_DEFLATED
import subprocess
import json
import pyzipper

class BackupThread(QThread):
    """Yedekleme işlemini ayrı bir thread'de yapar"""
    finished = pyqtSignal(int, int)  # total_copied, total_skipped
    error = pyqtSignal(str)
    progress = pyqtSignal(str)  # İlerleme durumu için

    def __init__(self, source_paths, backup_path, compress=False, encrypt=False, password=None):
        super().__init__()
        self.source_paths = source_paths
        self.backup_path = backup_path
        self.compress = compress
        self.encrypt = encrypt
        self.password = password  # password'ü encode etmeye gerek yok
        self._is_running = True

    def stop(self):
        """Thread'i durdur"""
        self._is_running = False
        self.progress.emit("Yedekleme işlemi durduruluyor...")
        
        # Thread'in durmasını bekle
        if self.isRunning():
            self.wait(2000)  # 2 saniye bekle
            if self.isRunning():  # Hala çalışıyorsa
                self.terminate()  # Zorla sonlandır
                self.wait()  # Sonlanmasını bekle
        
        # Yarım kalan dosyaları temizle
        try:
            if os.path.exists(self.backup_path):
                shutil.rmtree(self.backup_path, ignore_errors=True)
            
            # Yarım kalan zip dosyasını temizle
            zip_path = f"{self.backup_path}.zip"
            if os.path.exists(zip_path):
                os.remove(zip_path)
        except:
            pass

    def run(self):
        try:
            total_copied = 0
            total_skipped = 0
            
            # 1. AŞAMA: Normal Yedekleme
            for source_path in self.source_paths:
                # Durdurma kontrolü
                if not self._is_running:
                    self.progress.emit("Yedekleme işlemi durduruluyor...")
                    if os.path.exists(self.backup_path):
                        shutil.rmtree(self.backup_path, ignore_errors=True)
                    self.finished.emit(total_copied, total_skipped)
                    return

                if source_path.endswith('*'):
                    self.progress.emit(f"Klasör görmezden gelindi: {source_path}")
                    total_skipped += 1
                    continue
                
                folder_name = os.path.basename(source_path)
                target_path = os.path.join(self.backup_path, folder_name)
                
                try:
                    if os.path.exists(target_path):
                        shutil.rmtree(target_path, ignore_errors=True)
                    
                    self.progress.emit(f"Yedekleniyor: {source_path}")
                    
                    # Özel kopyalama fonksiyonu
                    def copy_with_retry(src, dst):
                        try:
                            if os.path.exists(dst):
                                shutil.rmtree(dst, ignore_errors=True)
                            
                            # Hedef klasörü oluştur
                            os.makedirs(dst, exist_ok=True)
                            
                            # Dosyaları kopyala
                            for root, dirs, files in os.walk(src):
                                # Durdurma kontrolü
                                if not self._is_running:
                                    return False
                                
                                # Klasörleri oluştur
                                for dir_name in dirs:
                                    if not self._is_running:  # Durdurma kontrolü
                                        return False
                                        
                                    src_dir = os.path.join(root, dir_name)
                                    dst_dir = os.path.join(dst, os.path.relpath(src_dir, src))
                                    try:
                                        os.makedirs(dst_dir, exist_ok=True)
                                    except:
                                        self.progress.emit(f"Klasör oluşturulamadı: {dst_dir}")
                                
                                # Dosyaları kopyala
                                for file_name in files:
                                    if not self._is_running:  # Durdurma kontrolü
                                        return False
                                        
                                    src_file = os.path.join(root, file_name)
                                    dst_file = os.path.join(dst, os.path.relpath(src_file, src))
                                    try:
                                        os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                                        shutil.copy2(src_file, dst_file)
                                    except Exception as e:
                                        self.progress.emit(f"Dosya kopyalanamadı: {src_file}")
                                        continue
                            return True
                        except Exception as e:
                            self.progress.emit(f"Kopyalama hatası: {str(e)}")
                            return False

                    # Kopyalama işlemini gerçekleştir
                    if copy_with_retry(source_path, target_path):
                        total_copied += 1
                        self.progress.emit(f"Klasör yedeklendi: {source_path}")
                    else:
                        # Durdurma kontrolü
                        if not self._is_running:
                            self.progress.emit("Yedekleme işlemi durduruluyor...")
                            if os.path.exists(self.backup_path):
                                shutil.rmtree(self.backup_path, ignore_errors=True)
                            self.finished.emit(total_copied, total_skipped)
                            return
                        
                        self.progress.emit(f"Klasör yedeklenemedi: {source_path}")
                        total_skipped += 1
                    
                except Exception as e:
                    self.progress.emit(f"Klasör yedeklenirken hata: {source_path} - {str(e)}")
                    total_skipped += 1
                    continue

                # Her klasör sonrası durdurma kontrolü
                if not self._is_running:
                    self.progress.emit("Yedekleme işlemi durduruluyor...")
                    if os.path.exists(self.backup_path):
                        shutil.rmtree(self.backup_path, ignore_errors=True)
                    self.finished.emit(total_copied, total_skipped)
                    return

            # 2. AŞAMA: Sıkıştırma ve Şifreleme
            if self.compress and total_copied > 0 and self._is_running:  # Durdurma kontrolü eklendi
                try:
                    self.progress.emit("Dosyalar sıkıştırılıyor...")
                    
                    # Zip dosyası yolunu oluştur
                    zip_path = f"{self.backup_path}.zip"
                    
                    # Eğer zip dosyası varsa sil
                    if os.path.exists(zip_path):
                        try:
                            os.remove(zip_path)
                        except:
                            pass
                    
                    # Zip dosyasını oluştur
                    if self.encrypt and self.password:
                        # Şifreli zip oluştur
                        self.progress.emit("Şifreli zip dosyası oluşturuluyor...")
                        with pyzipper.AESZipFile(zip_path,
                                               'w',
                                               compression=pyzipper.ZIP_DEFLATED,
                                               encryption=pyzipper.WZ_AES) as zf:
                            zf.setpassword(self.password.encode())
                            for root, dirs, files in os.walk(self.backup_path):
                                for file in files:
                                    try:
                                        file_path = os.path.join(root, file)
                                        arcname = os.path.relpath(file_path, os.path.dirname(self.backup_path))
                                        self.progress.emit(f"Sıkıştırılıyor: {arcname}")
                                        zf.write(file_path, arcname)
                                    except:
                                        continue
                        self.progress.emit("Şifreli zip dosyası oluşturuldu")
                    else:
                        # Normal zip oluştur
                        with ZipFile(zip_path, 'w', compression=ZIP_DEFLATED) as zipf:
                            for root, dirs, files in os.walk(self.backup_path):
                                # Durdurma kontrolü
                                if not self._is_running:
                                    break
                                    
                                for file in files:
                                    # Durdurma kontrolü
                                    if not self._is_running:
                                        break
                                    
                                    try:
                                        file_path = os.path.join(root, file)
                                        arcname = os.path.relpath(file_path, os.path.dirname(self.backup_path))
                                        self.progress.emit(f"Sıkıştırılıyor: {arcname}")
                                        zipf.write(file_path, arcname)
                                    except:
                                        continue
                        self.progress.emit("Zip dosyası oluşturuldu")
                    
                    # Durdurma kontrolü
                    if not self._is_running:
                        if os.path.exists(zip_path):
                            os.remove(zip_path)
                        self.progress.emit("Yedekleme işlemi durduruluyor...")
                        self.finished.emit(total_copied, total_skipped)
                        return
                    
                    self.progress.emit("Zip dosyası oluşturuldu")
                    
                    # Orijinal klasörü sil
                    if os.path.exists(self.backup_path):
                        shutil.rmtree(self.backup_path, ignore_errors=True)
                        self.progress.emit("Orijinal klasör silindi")
                    
                except Exception as e:
                    self.error.emit(f"Sıkıştırma hatası: {str(e)}")
                    return
            
            self.finished.emit(total_copied, total_skipped)
            
        except Exception as e:
            self.error.emit(str(e))

class BackupApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        
        # Terminal penceresini gizle (eğer exe olarak çalışıyorsa)
        if hasattr(sys, 'frozen'):
            import ctypes
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        
        # Model oluştur
        self.list_model = QtCore.QStringListModel()
        self.ui.listView.setModel(self.list_model)
        
        # ListView seçim değişikliğini izle
        self.ui.listView.selectionModel().selectionChanged.connect(self.on_selection_changed)
        
        # Sil butonuna tıklama olayını bağla
        self.ui.pushButton_2.clicked.connect(self.delete_selected_item)
        
        # Görmezden Gel butonuna tıklama olayını bağla
        self.ui.pushButton_3.clicked.connect(self.ignore_selected_item)
        
        # Ekle butonuna tıklama olayını bağla
        self.ui.pushButton.clicked.connect(self.add_folder)
        
        # Yedekle butonuna tıklama olayını bağla
        self.ui.pushButton_11.clicked.connect(self.toggle_backup)
        
        # Saat için timer oluştur
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Her 1 saniyede bir güncelle
        
        # Başlangıçta saati güncelle
        self.update_time()
        
        # Log dosyası ayarları
        self.setup_logging()
        
        # Başlangıçta diskleri listele
        self.list_removable_drives()
        
        # Başlangıç durumlarını ayarla
        self.set_initial_states()
        
        # Varsayılan klasörleri ekle
        self.add_default_folders()
        
        # Buton bağlantıları
        self.ui.pushButton_6.clicked.connect(self.refresh_drives)  # Yenile butonu
        self.ui.pushButton_5.clicked.connect(self.delete_key_file)  # Diski Sil butonu
        self.ui.checkBox_4.stateChanged.connect(self.toggle_folder_controls)  # Klasör düzenleme kontrolü
        self.ui.checkBox.stateChanged.connect(self.on_encrypt_changed)  # Şifrele
        self.ui.checkBox_2.stateChanged.connect(self.on_compress_changed)  # Sıkıştır
        
        # Yedekleme süresi için timer
        self.backup_timer = QtCore.QTimer()
        self.backup_timer.timeout.connect(self.update_backup_duration)
        self.backup_start_time = None
        
        self.backup_thread = None  # Yedekleme thread'i için değişken
        
        # Şifre kaydetme butonuna tıklama olayını bağla
        self.ui.pushButton_7.clicked.connect(self.save_default_password)
        
        # Başlangıçta varsayılan şifreyi yükle
        self.load_default_password()
        
        # Yedekleme durumu için değişken
        self.is_backup_running = False

    def update_time(self):
        """Anlık saati günceller"""
        current_time = datetime.now().strftime('%H:%M:%S') # Salise için son 4 haneyi al
        self.ui.label_4.setText(f"Saat: {current_time}")

    def setup_logging(self):
        """Log ayarlarını yapılandırır"""
        log_file = 'backup_log.txt'
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def check_key_file(self, mount_point):
        """Disk içinde .key dosyasını kontrol eder"""
        try:
            key_path = os.path.join(mount_point, '.key')
            if os.path.exists(key_path):
                with open(key_path, 'r') as key_file:
                    key_content = key_file.read().strip()
                    return key_content == "92047758821781743658436587323"
            return False
        except Exception as e:
            logging.error(f"Key dosyası kontrolünde hata: {str(e)}")
            return False

    def list_removable_drives(self):
        """Windows'ta çıkarılabilir diskleri tespit edip combobox'a ekler"""
        self.ui.comboBox_2.clear()
        
        try:
            # Tüm disk bölümlerini kontrol et
            for partition in psutil.disk_partitions(all=True):
                try:
                    # Sadece çıkarılabilir diskleri kontrol et
                    if 'removable' in partition.opts.lower():
                        drive_path = partition.mountpoint
                        try:
                            usage = psutil.disk_usage(drive_path)
                            total_size = usage.total / (1024 * 1024 * 1024)
                            disk_info = f"{drive_path} ({total_size:.1f} GB)"
                            
                            if self.check_key_file(drive_path):
                                self.ui.comboBox_2.addItem(disk_info, drive_path)
                                logging.info(f"Geçerli disk bulundu: {disk_info}")
                            else:
                                logging.warning(f"Geçersiz key dosyası: {disk_info}")
                        except Exception as e:
                            logging.error(f"Disk bilgisi alınamadı: {drive_path} - {str(e)}")
                            continue
                except Exception as e:
                    continue
                    
        except Exception as e:
            logging.error(f"Disk tarama hatası: {str(e)}")
            # Alternatif yöntem dene
            try:
                # Windows sürücü harflerini kontrol et
                for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                    drive = f"{letter}:\\"
                    try:
                        if os.path.exists(drive):
                            usage = psutil.disk_usage(drive)
                            if usage.total < 64 * 1024 * 1024 * 1024:  # 64GB'dan küçük diskleri çıkarılabilir kabul et
                                total_size = usage.total / (1024 * 1024 * 1024)
                                disk_info = f"{drive} ({total_size:.1f} GB)"
                                
                                if self.check_key_file(drive):
                                    self.ui.comboBox_2.addItem(disk_info, drive)
                                    logging.info(f"Geçerli disk bulundu: {disk_info}")
                                else:
                                    logging.warning(f"Geçersiz key dosyası: {disk_info}")
                    except:
                        continue
            except Exception as e:
                logging.error(f"Alternatif disk tarama hatası: {str(e)}")

    def delete_key_file(self):
        """Seçili diskteki .key dosyasını siler"""
        try:
            current_index = self.ui.comboBox_2.currentIndex()
            if current_index == -1:
                logging.warning("Disk seçilmedi")
                return

            mount_point = self.ui.comboBox_2.currentData()
            key_path = os.path.join(mount_point, '.key')

            if os.path.exists(key_path):
                os.remove(key_path)
                logging.info(f"Key dosyası silindi: {key_path}")
            else:
                logging.warning("Key dosyası bulunamadı")

            self.list_removable_drives()

        except Exception as e:
            logging.error(f"Key dosyası silinirken hata oluştu: {str(e)}")

    def refresh_drives(self):
        """Diskleri yeniden tarar ve listeler"""
        try:
            logging.info("Disk taraması başlatıldı")
            self.list_removable_drives()
            logging.info("Disk taraması tamamlandı")
        except Exception as e:
            logging.error(f"Disk yenileme hatası: {str(e)}")

    def set_initial_states(self):
        """Başlangıç durumlarını ayarlar"""
        # Butonları ve ListView'i devre dışı bırak
        self.ui.pushButton.setEnabled(False)
        self.ui.pushButton_2.setEnabled(False)
        self.ui.pushButton_3.setEnabled(False)
        self.ui.listView.setEnabled(False)
        
        # CheckBox'ı işaretsiz yap
        self.ui.checkBox_4.setChecked(False)
        
        logging.info("Başlangıç durumları ayarlandı")

    def toggle_folder_controls(self, state):
        """Klasör düzenleme kontrollerinin durumunu değiştirir"""
        try:
            # CheckBox işaretli ise kontrolleri etkinleştir
            is_enabled = state == 2  # Qt.Checked = 2
            
            self.ui.pushButton.setEnabled(is_enabled)
            self.ui.listView.setEnabled(is_enabled)
            
            # Sil ve Görmezden Gel butonları için ListView'de seçim kontrolü yap
            if is_enabled:
                has_selection = len(self.ui.listView.selectedIndexes()) > 0
                self.ui.pushButton_2.setEnabled(has_selection)
                self.ui.pushButton_3.setEnabled(has_selection)
            else:
                self.ui.pushButton_2.setEnabled(False)
                self.ui.pushButton_3.setEnabled(False)
            
            status = "etkinleştirildi" if is_enabled else "devre dışı bırakıldı"
            logging.info(f"Klasör düzenleme kontrolleri {status}")
            
        except Exception as e:
            logging.error(f"Klasör düzenleme kontrolleri değiştirilirken hata: {str(e)}")

    def add_default_folders(self):
        """Windows için varsayılan klasörleri ekler"""
        try:
            # Windows için özel klasör yolları
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
            documents = os.path.join(os.path.expanduser('~'), 'Documents')
            
            default_paths = [desktop, documents]
            
            # Var olan yolları kontrol et ve listeye ekle
            valid_paths = [path for path in default_paths if os.path.exists(path)]
            
            # Model'e ekle
            self.list_model.setStringList(valid_paths)
            
            logging.info(f"Varsayılan klasörler eklendi: {valid_paths}")
            
        except Exception as e:
            logging.error(f"Varsayılan klasörler eklenirken hata: {str(e)}")

    def on_selection_changed(self, selected, deselected):
        """ListView'de seçim değiştiğinde çalışır"""
        try:
            # Seçili öğe varsa butonları aktif et
            has_selection = len(self.ui.listView.selectedIndexes()) > 0
            if self.ui.checkBox_4.isChecked():  # Klasörleri düzenle işaretli ise
                self.ui.pushButton_2.setEnabled(has_selection)
                self.ui.pushButton_3.setEnabled(has_selection)
                
                # Seçili öğenin durumuna göre buton metnini güncelle
                if has_selection:
                    selected_index = self.ui.listView.selectedIndexes()[0]
                    current_text = self.list_model.data(selected_index, QtCore.Qt.DisplayRole)
                    if current_text.endswith('*'):
                        self.ui.pushButton_3.setText("Görmezden Gelme")
                    else:
                        self.ui.pushButton_3.setText("Görmezden Gel")
            
            if has_selection:
                logging.info("Listeden öğe seçildi")
            else:
                logging.info("Liste seçimi kaldırıldı")
                
        except Exception as e:
            logging.error(f"Seçim kontrolünde hata: {str(e)}")

    def delete_selected_item(self):
        """Listeden seçili öğeyi siler"""
        try:
            # Seçili indeksi al
            selected_indexes = self.ui.listView.selectedIndexes()
            if not selected_indexes:
                return
                
            # Seçili öğeyi al
            selected_index = selected_indexes[0]
            selected_item = self.list_model.data(selected_index, QtCore.Qt.DisplayRole)
            
            # Modelden öğeyi sil
            self.list_model.removeRow(selected_index.row())
            
            logging.info(f"Listeden silinen öğe: {selected_item}")
            
            # Seçim kaldırıldığında sil butonu otomatik olarak disable olacak
            
        except Exception as e:
            logging.error(f"Öğe silinirken hata: {str(e)}")

    def ignore_selected_item(self):
        """Seçili öğeyi görmezden gelir veya görmezden gelmeyi kaldırır"""
        try:
            # Seçili indeksi al
            selected_indexes = self.ui.listView.selectedIndexes()
            if not selected_indexes:
                return
                
            # Seçili öğeyi al
            selected_index = selected_indexes[0]
            current_text = self.list_model.data(selected_index, QtCore.Qt.DisplayRole)
            
            # Yıldız durumuna göre işlem yap
            if current_text.endswith('*'):
                # Yıldızı kaldır
                new_text = current_text[:-1]  # Son karakteri (*) kaldır
                self.ui.pushButton_3.setText("Görmezden Gel")
            else:
                # Yıldız ekle
                new_text = f"{current_text}*"
                self.ui.pushButton_3.setText("Görmezden Gelme")
            
            # Öğeyi güncelle
            self.list_model.setData(selected_index, new_text)
            
            action = "görmezden gelme kaldırıldı" if current_text.endswith('*') else "görmezden gelindi"
            logging.info(f"Öğe {action}: {current_text}")
            
        except Exception as e:
            logging.error(f"Öğe görmezden gelme işleminde hata: {str(e)}")

    def add_folder(self):
        """Klasör seçme dialogu açar ve seçilen klasörü listeye ekler"""
        try:
            # Klasör seçme dialogunu aç
            folder_path = QtWidgets.QFileDialog.getExistingDirectory(
                self,
                "Klasör Seç",
                os.path.expanduser('~'),  # Başlangıç dizini olarak home klasörü
                QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks
            )
            
            # Eğer klasör seçilmişse
            if folder_path:
                # Mevcut liste öğelerini al
                current_items = []
                for i in range(self.list_model.rowCount()):
                    item = self.list_model.data(self.list_model.index(i, 0), QtCore.Qt.DisplayRole)
                    current_items.append(item)
                
                # Eğer klasör zaten listede yoksa ekle
                if folder_path not in current_items:
                    current_items.append(folder_path)
                    self.list_model.setStringList(current_items)
                    logging.info(f"Yeni klasör eklendi: {folder_path}")
                else:
                    logging.warning(f"Klasör zaten listede mevcut: {folder_path}")
            else:
                logging.info("Klasör seçimi iptal edildi")
                
        except Exception as e:
            logging.error(f"Klasör ekleme hatası: {str(e)}")

    def toggle_password_controls(self, state):
        """Şifre kontrollerinin durumunu değiştirir"""
        try:
            # CheckBox işaretli ise kontrolleri etkinleştir
            is_enabled = state == 2  # Qt.Checked = 2
            
            self.ui.lineEdit.setEnabled(is_enabled)
            self.ui.pushButton_7.setEnabled(is_enabled)
            
            status = "etkinleştirildi" if is_enabled else "devre dışı bırakıldı"
            logging.info(f"Şifre kontrolleri {status}")
            
        except Exception as e:
            logging.error(f"Şifre kontrolleri değiştirilirken hata: {str(e)}")

    def disable_all_controls(self):
        """Tüm kontrolleri devre dışı bırakır"""
        # ComboBox'lar
        self.ui.comboBox_2.setEnabled(False)
        
        # CheckBox'lar
        self.ui.checkBox.setEnabled(False)
        self.ui.checkBox_2.setEnabled(False)
        self.ui.checkBox_4.setEnabled(False)
        
        # LineEdit'ler
        self.ui.lineEdit.setEnabled(False)
        self.ui.lineEdit_2.setEnabled(False)
        
        # Butonlar
        self.ui.pushButton.setEnabled(False)
        self.ui.pushButton_2.setEnabled(False)
        self.ui.pushButton_3.setEnabled(False)
        self.ui.pushButton_5.setEnabled(False)
        self.ui.pushButton_6.setEnabled(False)
        self.ui.pushButton_7.setEnabled(False)
        self.ui.pushButton_8.setEnabled(False)
        
        # Yedekle butonunun metnini değiştir
        self.ui.pushButton_11.setText("Yedeklemeyi Durdur")
        
        # ListView
        self.ui.listView.setEnabled(False)

    def enable_all_controls(self):
        """Tüm kontrolleri tekrar etkinleştirir"""
        # ComboBox'lar
        self.ui.comboBox_2.setEnabled(True)
        
        # CheckBox'lar
        self.ui.checkBox.setEnabled(True)
        self.ui.checkBox_2.setEnabled(True)
        self.ui.checkBox_4.setEnabled(True)
        
        # LineEdit'ler
        self.ui.lineEdit.setEnabled(self.ui.checkBox.isChecked())  # Şifreleme durumuna göre
        self.ui.lineEdit_2.setEnabled(True)
        
        # Butonlar
        self.ui.pushButton_5.setEnabled(True)
        self.ui.pushButton_6.setEnabled(True)
        self.ui.pushButton_7.setEnabled(self.ui.checkBox.isChecked())  # Şifreleme durumuna göre
        self.ui.pushButton_8.setEnabled(True)
        self.ui.pushButton_11.setEnabled(True)
        
        # Klasör düzenleme durumuna göre kontrolleri ayarla
        self.toggle_folder_controls(2 if self.ui.checkBox_4.isChecked() else 0)

    def update_backup_duration(self):
        """Yedekleme süresini günceller"""
        if self.backup_start_time:
            elapsed = datetime.now() - self.backup_start_time
            hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.ui.label_6.setText(f"Süre: {hours:02d}:{minutes:02d}:{seconds:02d}")

    def on_encrypt_changed(self, state):
        """Şifrele checkbox'ı değiştiğinde çalışır"""
        try:
            is_checked = state == 2  # Qt.Checked = 2
            
            # Şifreleme seçilirse sıkıştırmayı da otomatik seç
            if is_checked:
                self.ui.checkBox_2.setChecked(True)
            
            # Şifre kontrollerini güncelle
            self.toggle_password_controls(state)
            
            logging.info(f"Şifreleme {'etkinleştirildi' if is_checked else 'devre dışı bırakıldı'}")
            
        except Exception as e:
            logging.error(f"Şifreleme durumu değiştirilirken hata: {str(e)}")

    def on_compress_changed(self, state):
        """Sıkıştır checkbox'ı değiştiğinde çalışır"""
        try:
            is_checked = state == 2  # Qt.Checked = 2
            
            # Sıkıştırma kaldırılırsa şifrelemeyi de kaldır
            if not is_checked and self.ui.checkBox.isChecked():
                self.ui.checkBox.setChecked(False)
            
            logging.info(f"Sıkıştırma {'etkinleştirildi' if is_checked else 'devre dışı bırakıldı'}")
            
        except Exception as e:
            logging.error(f"Sıkıştırma durumu değiştirilirken hata: {str(e)}")

    def toggle_backup(self):
        """Yedeklemeyi başlat veya durdur"""
        if not self.is_backup_running:
            self.start_backup()
        else:
            self.stop_backup()

    def start_backup(self):
        """Seçili klasörleri yedekler"""
        try:
            # Disk seçili mi kontrol et
            current_disk_index = self.ui.comboBox_2.currentIndex()
            if current_disk_index == -1:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Uyarı",
                    "Lütfen bir disk seçin!"
                )
                return

            # Sıkıştırma ve şifreleme durumlarını kontrol et
            is_compress = self.ui.checkBox_2.isChecked()
            is_encrypt = self.ui.checkBox.isChecked()
            
            # Şifreleme seçili ise şifre kontrolü yap
            if is_encrypt:
                password = self.ui.lineEdit.text()
                if not password:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "Uyarı",
                        "Şifreleme seçili iken şifre boş olamaz!"
                    )
                    return

            # Hedef disk yolunu al
            target_disk = self.ui.comboBox_2.currentData()
            
            # Backup klasörünü kontrol et/oluştur
            backup_folder = os.path.join(target_disk, "Backup")
            if not os.path.exists(backup_folder):
                os.makedirs(backup_folder)

            # Bugünün tarihiyle klasör oluştur
            current_date = datetime.now().strftime('%d.%m.%Y')
            date_folder = os.path.join(backup_folder, current_date)
            if not os.path.exists(date_folder):
                os.makedirs(date_folder)

            # Bilgisayar adıyla klasör oluştur
            pc_name = self.ui.lineEdit_2.text()
            backup_path = os.path.join(date_folder, pc_name)

            # Yedeklenecek klasörleri al
            source_paths = []
            for i in range(self.list_model.rowCount()):
                path = self.list_model.data(self.list_model.index(i, 0), QtCore.Qt.DisplayRole)
                source_paths.append(path)

            # Yedekleme thread'ini başlat
            self.backup_thread = BackupThread(
                source_paths=source_paths,
                backup_path=backup_path,
                compress=is_compress,
                encrypt=is_encrypt,
                password=self.ui.lineEdit.text() if is_encrypt else None
            )
            
            # Thread sinyallerini bağla
            self.backup_thread.finished.connect(self.on_backup_finished)
            self.backup_thread.error.connect(self.on_backup_error)
            self.backup_thread.progress.connect(self.on_backup_progress)
            
            # Thread'i başlat
            self.backup_thread.start()
            
            # Kontrolleri devre dışı bırak
            self.disable_all_controls()
            
            # Yedekleme durumunu güncelle
            self.is_backup_running = True
            self.ui.pushButton_11.setText("Yedeklemeyi Durdur")
            
            # Yedekleme başlangıç zamanını ayarla
            self.backup_start_time = datetime.now()
            self.ui.label_5.setText(f"Başlangıç Saati: {self.backup_start_time.strftime('%H:%M:%S')}")
            
            # Süre sayacını başlat
            self.backup_timer.start(1000)
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Hata",
                f"Yedekleme başlatılırken hata oluştu: {str(e)}"
            )

    def stop_backup(self):
        """Yedekleme işlemini durdurur"""
        try:
            if self.backup_thread and self.backup_thread.isRunning():
                # Kullanıcıya sor
                reply = QtWidgets.QMessageBox.question(
                    self,
                    'Yedeklemeyi Durdur',
                    'Yedekleme işlemi durdurulacak. Emin misiniz?',
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No
                )
                
                if reply == QtWidgets.QMessageBox.Yes:
                    self.backup_thread.stop()
                    self.is_backup_running = False
                    self.ui.pushButton_11.setText("Yedekle")
                    self.enable_all_controls()
                    self.backup_timer.stop()
                    logging.info("Yedekleme kullanıcı tarafından durduruldu")
        except Exception as e:
            logging.error(f"Yedekleme durdurulurken hata: {str(e)}")

    def on_backup_finished(self, total_copied, total_skipped):
        """Yedekleme tamamlandığında çalışır"""
        self.backup_timer.stop()
        self.backup_start_time = None
        self.update_backup_duration()
        self.enable_all_controls()
        self.ui.pushButton_11.setText("Yedekle")
        self.is_backup_running = False
        logging.info(f"Yedekleme tamamlandı. Kopyalanan: {total_copied}, Atlanan: {total_skipped}")

    def on_backup_error(self, error_message):
        """Yedekleme hatası olduğunda çalışır"""
        self.backup_timer.stop()
        self.backup_start_time = None
        self.enable_all_controls()
        self.ui.pushButton_11.setText("Yedekle")
        self.is_backup_running = False
        logging.error(f"Yedekleme işleminde hata: {error_message}")

    def on_backup_progress(self, message):
        """Yedekleme ilerlemesini loglar"""
        logging.info(message)

    def save_default_password(self):
        """Varsayılan şifreyi kaydeder"""
        try:
            # Yeni şifreyi al
            new_password = self.ui.lineEdit.text()
            
            if not new_password:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Şifre Hatası",
                    "Boş şifre kaydedilemez!"
                )
                return
            
            # Config dosyasını oluştur/güncelle
            config = {
                'default_password': new_password
            }
            
            # Config klasörünü kontrol et/oluştur
            config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            # Config dosyasına kaydet
            config_file = os.path.join(config_dir, 'backup_config.json')
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            
            QtWidgets.QMessageBox.information(
                self,
                "Başarılı",
                "Varsayılan şifre kaydedildi!"
            )
            logging.info("Varsayılan şifre güncellendi")
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Hata",
                f"Şifre kaydedilirken hata oluştu: {str(e)}"
            )
            logging.error(f"Şifre kaydetme hatası: {str(e)}")

    def load_default_password(self):
        """Varsayılan şifreyi yükler"""
        try:
            # Config dosyasının yolunu al
            config_file = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                'config', 
                'backup_config.json'
            )
            
            # Eğer config dosyası varsa
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    default_password = config.get('default_password', '112.st!?')
            else:
                default_password = '112.st!?'  # Varsayılan şifre
            
            # Şifreyi line edit'e yaz
            self.ui.lineEdit.setText(default_password)
            logging.info("Varsayılan şifre yüklendi")
            
        except Exception as e:
            logging.error(f"Varsayılan şifre yükleme hatası: {str(e)}")
            # Hata durumunda varsayılan şifreyi kullan
            self.ui.lineEdit.setText('112.st!?')

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = BackupApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 