# SecureVault Mobile Apps

This directory contains the mobile applications for SecureVault.

## iOS App

The iOS app is built using Swift and UIKit, providing native iOS experience with:

- Biometric authentication (Face ID/Touch ID)
- Secure Enclave integration
- iOS Keychain integration
- Auto-fill credential provider
- Siri Shortcuts support

### Development Setup

1. Open `ios/SecureVault.xcodeproj` in Xcode
2. Configure your development team and bundle identifier
3. Build and run on device or simulator

### Requirements

- Xcode 14.0+
- iOS 15.0+
- Swift 5.7+

## Android App

The Android app is built using Kotlin and follows Material Design guidelines:

- Biometric authentication (Fingerprint/Face unlock)
- Android Keystore integration
- Autofill service provider
- App shortcuts support
- Dark/Light theme support

### Development Setup

1. Open `android/` directory in Android Studio
2. Sync Gradle files
3. Build and run on device or emulator

### Requirements

- Android Studio Arctic Fox+
- Android API 26+ (Android 8.0)
- Kotlin 1.7+

## API Integration

Both mobile apps communicate with the SecureVault server using the Mobile API endpoints:

- `/api/mobile/auth/login` - Authentication
- `/api/mobile/credentials` - Credential management
- `/api/mobile/sync` - Data synchronization
- `/api/mobile/search` - Credential search

## Security Features

### iOS Security
- Secure Enclave for key storage
- Keychain Services for credential storage
- App Transport Security (ATS)
- Certificate pinning
- Jailbreak detection

### Android Security
- Android Keystore for key storage
- EncryptedSharedPreferences for data storage
- Network Security Config
- Certificate pinning
- Root detection

## Build Instructions

### iOS Build

```bash
cd ios/
xcodebuild -project SecureVault.xcodeproj -scheme SecureVault -configuration Release
```

### Android Build

```bash
cd android/
./gradlew assembleRelease
```

## Distribution

### iOS App Store

1. Archive the app in Xcode
2. Upload to App Store Connect
3. Submit for review

### Google Play Store

1. Generate signed APK/AAB
2. Upload to Google Play Console
3. Submit for review

## Testing

### iOS Testing

```bash
cd ios/
xcodebuild test -project SecureVault.xcodeproj -scheme SecureVault -destination 'platform=iOS Simulator,name=iPhone 14'
```

### Android Testing

```bash
cd android/
./gradlew test
./gradlew connectedAndroidTest
```

## Contributing

Please read the main CONTRIBUTING.md file for guidelines on contributing to the mobile apps.

## License

Same as the main SecureVault project - MIT License.
