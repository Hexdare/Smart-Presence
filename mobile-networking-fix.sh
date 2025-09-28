#!/bin/bash

echo "🔧 Fixing Mobile App Networking Issues"
echo "====================================="

# Check if we're in the frontend directory
if [ ! -f "package.json" ]; then
    echo "❌ Please run this script from your frontend directory"
    exit 1
fi

echo "📱 Step 1: Installing HTTP plugin..."
npm install @capacitor/http

echo "📱 Step 2: Creating network security config..."
mkdir -p android/app/src/main/res/xml
cp ../network_security_config.xml android/app/src/main/res/xml/

echo "📱 Step 3: Updating AndroidManifest.xml..."
# Add network permissions and config to AndroidManifest.xml
MANIFEST_FILE="android/app/src/main/AndroidManifest.xml"

if [ -f "$MANIFEST_FILE" ]; then
    # Add network security config if not already present
    if ! grep -q "networkSecurityConfig" "$MANIFEST_FILE"; then
        sed -i 's/<application/<application\n        android:networkSecurityConfig="@xml\/network_security_config"/' "$MANIFEST_FILE"
        echo "✅ Added network security config to AndroidManifest.xml"
    fi
    
    # Add internet permission if not already present
    if ! grep -q "android.permission.INTERNET" "$MANIFEST_FILE"; then
        sed -i '/<uses-permission android:name="android.permission.INTERNET" \/>/a\    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />\n    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />' "$MANIFEST_FILE"
        echo "✅ Added network permissions to AndroidManifest.xml"
    fi
else
    echo "⚠️  AndroidManifest.xml not found. Please run 'npx cap add android' first."
fi

echo "📱 Step 4: Building and syncing..."
npm run build
npx cap sync android

echo "✅ Mobile networking fixes applied!"
echo ""
echo "📋 Next Steps:"
echo "1. Copy network_security_config.xml to android/app/src/main/res/xml/"
echo "2. Update your API calls to use the new ApiClient"
echo "3. Rebuild APK in Android Studio"
echo "4. Test on physical device"
echo ""
echo "📱 Open Android Studio:"
echo "npx cap open android"