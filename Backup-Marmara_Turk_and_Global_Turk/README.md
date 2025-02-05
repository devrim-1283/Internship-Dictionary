# Backup Uygulaması

Bu uygulama, dosyalarınızı yedeklemek için geliştirilmiş bir araçtır. Hem Linux hem de Windows işletim sistemlerinde çalışabilir.

## Özellikler

- **Çoklu Platform Desteği**: Uygulama hem Linux hem de Windows üzerinde çalışabilir.
- **Kullanıcı Dostu Arayüz**: PyQt5 ile geliştirilmiş grafiksel kullanıcı arayüzü.
- **Yedekleme ve Sıkıştırma**: Dosyalarınızı yedeklerken sıkıştırma ve şifreleme seçenekleri sunar.
- **Çıkarılabilir Disk Desteği**: USB bellekler gibi çıkarılabilir diskleri otomatik olarak algılar.
- **Loglama**: Yedekleme işlemleri sırasında oluşan olayları kaydeder.

## Kullanılan Kütüphaneler

- **PyQt5**: Kullanıcı arayüzü oluşturmak için.
- **psutil**: Sistem bilgilerini almak için.
- **shutil**: Dosya ve dizin işlemleri için.
- **zipfile** ve **pyminizip**: Dosyaları sıkıştırmak ve şifrelemek için.
- **json**: Yapılandırma dosyalarını okumak ve yazmak için.
- **logging**: Uygulama olaylarını kaydetmek için.

## Kurulum

### Windows

1. Python 3.8 veya daha yüksek bir sürümü yükleyin.
2. Gerekli Python paketlerini yükleyin:
   ```bash
   pip install PyQt5 psutil pyminizip
   ```
3. `installer.py` dosyasını çalıştırarak uygulamayı kurun.

### Linux

1. Python 3.6 veya daha yüksek bir sürümü yükleyin.
2. Gerekli Python paketlerini yükleyin:
   ```bash
   pip install PyQt5 psutil pyminizip
   ```
3. `install.py` dosyasını çalıştırarak uygulamayı kurun.

## Kullanım

Uygulamayı başlattıktan sonra, yedeklemek istediğiniz klasörleri seçebilir, sıkıştırma ve şifreleme seçeneklerini ayarlayabilirsiniz. Yedekleme işlemi sırasında ilerleme durumu ve loglar görüntülenir.

## İletişim

Herhangi bir sorunuz veya geri bildiriminiz varsa, lütfen benimle iletişime geçin:
- [E-posta adresinizi buraya ekleyin]

## Lisans

Bu proje, [Lisans bilgilerinizi buraya ekleyin] lisansı altında lisanslanmıştır. 