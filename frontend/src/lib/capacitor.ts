import { Capacitor } from "@capacitor/core";

/** True when running inside an iOS or Android native shell */
export const isNative = () => Capacitor.isNativePlatform();

/** Current platform: "ios" | "android" | "web" */
export const getPlatform = () => Capacitor.getPlatform();

export const isIOS = () => Capacitor.getPlatform() === "ios";
export const isAndroid = () => Capacitor.getPlatform() === "android";
export const isWeb = () => Capacitor.getPlatform() === "web";

/**
 * Call once at app startup (e.g. in a root layout useEffect).
 * Configures StatusBar, Keyboard, and SplashScreen for native platforms.
 */
export const initNativePlugins = setupNativeFeatures;

export async function setupNativeFeatures() {
  if (!isNative()) return;

  // StatusBar
  const { StatusBar, Style } = await import("@capacitor/status-bar");
  await StatusBar.setStyle({ style: Style.Dark });
  if (isAndroid()) {
    await StatusBar.setBackgroundColor({ color: "#0f172a" });
  }

  // Keyboard
  const { Keyboard } = await import("@capacitor/keyboard");
  Keyboard.addListener("keyboardWillShow", () => {
    document.body.classList.add("keyboard-open");
  });
  Keyboard.addListener("keyboardWillHide", () => {
    document.body.classList.remove("keyboard-open");
  });

  // SplashScreen — hide after native features are ready
  const { SplashScreen } = await import("@capacitor/splash-screen");
  await SplashScreen.hide();
}
