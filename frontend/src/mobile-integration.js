// Mobile Integration for QR Attendance App
// This file contains mobile-specific enhancements

import { Capacitor } from '@capacitor/core';
import { StatusBar, Style } from '@capacitor/status-bar';
import { App as CapacitorApp } from '@capacitor/app';
import { Haptics, ImpactStyle } from '@capacitor/haptics';

export class MobileIntegration {
  static async initialize() {
    if (!Capacitor.isNativePlatform()) {
      console.log('Running on web - mobile features disabled');
      return;
    }

    try {
      // Configure status bar
      await StatusBar.setStyle({ style: Style.Dark });
      await StatusBar.setBackgroundColor({ color: '#1f2937' });
      
      // Handle Android back button
      CapacitorApp.addListener('backButton', ({ canGoBack }) => {
        if (!canGoBack) {
          CapacitorApp.exitApp();
        } else {
          window.history.back();
        }
      });

      // App state listeners
      CapacitorApp.addListener('appStateChange', ({ isActive }) => {
        console.log('App state changed. Is active?', isActive);
      });

      console.log('Mobile integration initialized successfully');
    } catch (error) {
      console.error('Mobile integration failed:', error);
    }
  }

  static async vibrate(type = 'light') {
    if (!Capacitor.isNativePlatform()) return;
    
    try {
      const impactStyle = type === 'heavy' ? ImpactStyle.Heavy : 
                         type === 'medium' ? ImpactStyle.Medium : 
                         ImpactStyle.Light;
      
      await Haptics.impact({ style: impactStyle });
    } catch (error) {
      console.log('Haptics not available');
    }
  }

  static isMobile() {
    return Capacitor.isNativePlatform();
  }

  static getPlatform() {
    return Capacitor.getPlatform();
  }

  // Enhanced QR Scanner for mobile
  static async requestCameraPermission() {
    if (!Capacitor.isNativePlatform()) return true;
    
    try {
      // Camera permission is handled by the QR scanner library
      // This is a placeholder for future permission handling
      return true;
    } catch (error) {
      console.error('Camera permission error:', error);
      return false;
    }
  }

  // Mobile-specific UI adjustments
  static getMobileStyles() {
    if (!this.isMobile()) return {};
    
    return {
      // Add safe area padding for notched phones
      paddingTop: 'env(safe-area-inset-top)',
      paddingBottom: 'env(safe-area-inset-bottom)',
      paddingLeft: 'env(safe-area-inset-left)',
      paddingRight: 'env(safe-area-inset-right)',
    };
  }

  // Show mobile-optimized notifications
  static showMobileNotification(title, message, type = 'success') {
    // Use native toast or notification if available
    // Fallback to web notification
    console.log(`Mobile Notification: ${title} - ${message}`);
    
    // Trigger haptic feedback
    if (type === 'success') {
      this.vibrate('light');
    } else if (type === 'error') {
      this.vibrate('heavy');
    }
  }
}

// Export for use in main App.js
export default MobileIntegration;