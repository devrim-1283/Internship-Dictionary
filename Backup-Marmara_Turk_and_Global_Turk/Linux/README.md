# Backup Uygulaması Kurulum Kılavuzu (Linux)

## Gereksinimler

Kurulum yapmadan önce aşağıdaki yazılımların bilgisayarınızda yüklü olduğundan emin olun:

1. Python 3.6 veya daha yüksek bir sürüm
   - Python genellikle çoğu Linux dağıtımında önceden yüklü gelir

## Kurulum Adımları

1. Dosyaları bilgisayarınıza indirin
   - `install.py`
   - `main.py`
   - `backup_ui.py`
   - `icon_backup.png` (isteğe bağlı)
   - Tüm dosyaların aynı klasörde olduğundan emin olun

2. Kurulumu başlatın
   - Terminali açın ve dosyaların bulunduğu dizine gidin
   - Aşağıdaki komutu çalıştırarak kurulumu başlatın:
     ```bash
     python3 install.py
     ```

3. Kurulum sihirbazını takip edin
   - Gerekli dosyaların kopyalanması ve yapılandırma dosyalarının oluşturulması otomatik olarak yapılacaktır

## Kurulum Sonrası

Kurulum tamamlandığında:
- Program `~/.local/share/backup-app` klasörüne kurulacak
- `~/.local/bin` dizininde çalıştırılabilir bir dosya oluşturulacak
- Uygulama menüsünde bir giriş oluşturulacak

## Sorun Giderme

1. "Error: Required file not found" hatası alırsanız:
   - Tüm gerekli dosyaların aynı klasörde olduğundan emin olun

2. Uygulama menüsünde simge görünmüyorsa:
   - Oturumu kapatıp tekrar açmayı deneyin

3. Kurulum sırasında hata alırsanız:
   - Terminaldeki hata mesajlarını kontrol edin
   - Gerekli izinlerin verildiğinden emin olun

## İletişim

Herhangi bir sorun yaşarsanız veya yardıma ihtiyacınız olursa:
[İletişim bilgilerinizi buraya ekleyin]

## Lisans

[Lisans bilgilerinizi buraya ekleyin] 