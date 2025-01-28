# 🔒 Secure Backup Application

<p align="center">
  <img src="icon_backup.ico" alt="Backup App Logo" width="200"/>
</p>

A secure and user-friendly backup application with encryption capabilities, designed for Windows. Built with Python and PyQt5.

## 🌟 Key Features

- 🔐 **AES Encryption**: Military-grade encryption for your sensitive data
- 📦 **Smart Compression**: Reduce backup size while maintaining data integrity
- 💾 **USB Security**: Secure USB verification with key file system
- 🔄 **Real-time Progress**: Monitor backup progress in real-time
- 🎯 **Simple Interface**: User-friendly design for easy operation
- 🚀 **Quick Setup**: Easy installation process with auto-configuration

## 📋 Requirements

- Windows 10/11
- Python 3.8 or higher
- 100MB free disk space
- USB drive for backup storage

## ⚡ Quick Start Guide

### 1. Clone Repository
```bash
git clone https://github.com/devrimtuner/backup-application.git
cd backup-application
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
- PyQt5
- pyzipper
- psutil
- pywin32

### 3. Run Installer
```bash
python installer.py
```

The installer will:
- Create configuration files
- Generate USB key file
- Compile the application
- Create shortcuts
- Configure autostart (optional)

## 🎮 How to Use

1. **Initial Setup**
   - Copy `.key` file from Downloads to your USB drive
   - Insert USB drive into computer
   - Launch Backup App from desktop shortcut

2. **Configure Backup**
   - Select target USB drive
   - Choose folders to backup
   - Enable encryption if needed
   - Set compression options

3. **Start Backup**
   - Click "Backup" button
   - Monitor progress
   - Wait for completion notification

## 🔧 Advanced Configuration

### USB Key File
- Location: Root of USB drive
- Filename: `.key`
- Must match security verification

### Default Settings
- Backup Location: `USB_DRIVE/Backup/DATE/COMPUTER_NAME`
- Default Password: `123456`
- Auto-selected Folders: Desktop, Documents

## 🛟 Troubleshooting

1. **USB Not Detected**
   - Verify `.key` file is present
   - Check USB connection
   - Try refreshing drive list

2. **Backup Fails**
   - Ensure sufficient disk space
   - Check folder permissions
   - Verify USB is not write-protected

## 👥 Development Team

- **Devrim Tunçer** - Lead Developer
- **Esma Tanşa** - Developer

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📞 Support

For support:
- Create an issue in repository
- Email: devrimtuncer@example.com

---
<p align="center">
  Made with ❤️ by Devrim Tunçer & Esma Tanşa
</p>

