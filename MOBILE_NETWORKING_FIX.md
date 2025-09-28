# 🔧 Mobile App Networking Fix Guide

## 🚨 **Issue**: Mobile app can't connect to backend (login/register fails)

This is a common issue when converting web apps to mobile. Here are the fixes:

---

## 🔍 **Diagnosis Steps**

### **1. Check Your Backend URL**
Current backend URL in `.env`: `https://phone-app-deploy-1.preview.emergentagent.com`

**Test the backend URL:**
```bash
# Test if backend is accessible
curl https://phone-app-deploy-1.preview.emergentagent.com/api/auth/me
```

---

## 🛠️ **Fix 1: Update Android Network Security Config** 

Create: `android/app/src/main/res/xml/network_security_config.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">phone-app-deploy-1.preview.emergentagent.com</domain>
        <domain includeSubdomains="true">smart-attendance-system-ur85.onrender.com</domain>
        <domain includeSubdomains="true">localhost</domain>
        <domain includeSubdomains="true">10.0.2.2</domain>
    </domain-config>
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <certificates src="system"/>
        </trust-anchors>
    </base-config>
</network-security-config>
```

### **Update AndroidManifest.xml**
Add to `<application>` tag in `android/app/src/main/AndroidManifest.xml`:

```xml
<application
    android:networkSecurityConfig="@xml/network_security_config"
    ... other attributes>
```

---

## 🛠️ **Fix 2: Add Network Permissions**

Update `android/app/src/main/AndroidManifest.xml`:

```xml
<!-- Add these permissions before <application> -->
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
<uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />

<!-- For debugging network issues -->
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
```

---

## 🛠️ **Fix 3: Update Capacitor Config**

Update `capacitor.config.json`:

```json
{
  "appId": "com.attendance.qrapp",
  "appName": "QR Attendance",
  "webDir": "build",
  "server": {
    "androidScheme": "https",
    "allowNavigation": [
      "phone-app-deploy-1.preview.emergentagent.com",
      "smart-attendance-system-ur85.onrender.com"
    ]
  },
  "plugins": {
    "Camera": {
      "permissions": ["camera"]
    },
    "StatusBar": {
      "style": "DARK",
      "backgroundColor": "#1f2937"
    },
    "CapacitorHttp": {
      "enabled": true
    }
  }
}
```

---

## 🛠️ **Fix 4: Use Native HTTP Plugin**

### **Install HTTP Plugin:**
```bash
npm install @capacitor/http
```

### **Update API calls in your React app:**

Create: `src/api-client.js`

```javascript
import { CapacitorHttp } from '@capacitor/http';
import { Capacitor } from '@capacitor/core';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL?.replace(/\/$/, '') || "";

class ApiClient {
  static async request(url, options = {}) {
    const fullUrl = `${BACKEND_URL}${url}`;
    
    if (Capacitor.isNativePlatform()) {
      // Use Capacitor HTTP for mobile
      const response = await CapacitorHttp.request({
        url: fullUrl,
        method: options.method || 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        data: options.body ? JSON.parse(options.body) : undefined
      });
      
      return {
        ok: response.status >= 200 && response.status < 300,
        status: response.status,
        json: async () => response.data,
        text: async () => JSON.stringify(response.data)
      };
    } else {
      // Use fetch for web
      return fetch(fullUrl, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        }
      });
    }
  }

  static async get(url, headers = {}) {
    return this.request(url, { method: 'GET', headers });
  }

  static async post(url, data, headers = {}) {
    return this.request(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(data)
    });
  }
}

export default ApiClient;
```

### **Update your login/register functions:**

Replace axios calls with ApiClient:

```javascript
// OLD WAY (with axios):
// const response = await axios.post(`${API}/auth/login`, { username, password });

// NEW WAY (with ApiClient):
const response = await ApiClient.post('/auth/login', { username, password });
const data = await response.json();
```

---

## 🛠️ **Fix 5: Debug Network Issues**

### **Add debugging to your App.js:**

```javascript
import { Capacitor } from '@capacitor/core';

// Add this to your App component
useEffect(() => {
  if (Capacitor.isNativePlatform()) {
    console.log('Running on mobile platform:', Capacitor.getPlatform());
    console.log('Backend URL:', process.env.REACT_APP_BACKEND_URL);
    
    // Test network connectivity
    testNetworkConnection();
  }
}, []);

const testNetworkConnection = async () => {
  try {
    const response = await fetch(process.env.REACT_APP_BACKEND_URL + '/health', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    console.log('Network test result:', response.status);
  } catch (error) {
    console.error('Network test failed:', error);
  }
};
```

---

## 🚀 **Quick Fix Steps**

### **Step 1: Apply Fixes**
```bash
# 1. Update capacitor config (see Fix 3 above)
# 2. Add network security config (see Fix 1 above)  
# 3. Update AndroidManifest.xml (see Fix 2 above)

# 4. Install HTTP plugin
npm install @capacitor/http

# 5. Rebuild and sync
npm run build
npx cap sync android
```

### **Step 2: Test Backend Connectivity**
```bash
# Test if your backend is working
curl -X POST https://phone-app-deploy-1.preview.emergentagent.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'
```

### **Step 3: Rebuild APK**
```bash
# In Android Studio:
# Build > Clean Project
# Build > Rebuild Project  
# Build > Build APK(s)
```

---

## 🔍 **Testing Checklist**

- [ ] Backend URL is correct and accessible
- [ ] Network security config added
- [ ] Internet permissions added
- [ ] Capacitor HTTP plugin installed
- [ ] App rebuilt and synced
- [ ] APK regenerated and installed
- [ ] Test on physical device (not emulator)

---

## 🆘 **Still Not Working?**

### **Alternative Backend URLs to try:**
```javascript
// If current URL doesn't work, try:
REACT_APP_BACKEND_URL=https://smart-attendance-system-ur85.onrender.com/api
```

### **Enable HTTP (if backend doesn't have SSL):**
Add to network security config:
```xml
<domain-config cleartextTrafficPermitted="true">
    <domain includeSubdomains="true">your-backend-domain.com</domain>
</domain-config>
```

### **Check Android Logs:**
```bash
# Connect phone via USB and run:
adb logcat | grep -i "network\|http\|error"
```

---

## ✅ **Expected Result**
After applying these fixes, your mobile app should successfully connect to the backend and allow login/registration just like the web version!