#!/bin/bash

# QR Attendance Mobile App Conversion Script
# This script converts your React web app into a mobile APK

echo "🚀 QR Attendance Mobile App Conversion"
echo "====================================="

# Check if we're in the frontend directory
if [ ! -f "package.json" ]; then
    echo "❌ Please run this script from your frontend directory"
    exit 1
fi

echo "📱 Step 1: Installing Capacitor dependencies..."
npm install @capacitor/core @capacitor/cli @capacitor/android
npm install @capacitor/camera @capacitor/app @capacitor/haptics @capacitor/status-bar

echo "📱 Step 2: Initializing Capacitor..."
npx cap init "QR Attendance" "com.attendance.qrapp" --web-dir=build

echo "📱 Step 3: Adding Android platform..."
npx cap add android

echo "📱 Step 4: Building React app..."
npm run build

echo "📱 Step 5: Syncing with Capacitor..."
npx cap sync android

echo "✅ Mobile app setup complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Install Android Studio: https://developer.android.com/studio"
echo "2. Open your project: npx cap open android"
echo "3. Build APK from Android Studio"
echo ""
echo "🎯 Your mobile app features:"
echo "   • QR camera scanner"
echo "   • Student/Teacher/Principal roles"
echo "   • Emergency alerts"
echo "   • Announcements"
echo "   • Offline-ready design"