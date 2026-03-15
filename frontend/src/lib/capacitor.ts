import { Capacitor } from "@capacitor/core";

export const isNative = Capacitor.isNativePlatform();
export const platform = Capacitor.getPlatform(); // "ios" | "android" | "web"

export async function initNativePlugins() {
  if (!isNative) return;

  const { StatusBar, Style } = await import("@capacitor/status-bar");
  const { Keyboard } = await import("@capacitor/keyboard");

  await StatusBar.setStyle({ style: Style.Dark });

  if (platform === "android") {
    await StatusBar.setBackgroundColor({ color: "#0f172a" });
  }

  Keyboard.addListener("keyboardWillShow", () => {
    document.body.classList.add("keyboard-open");
  });
  Keyboard.addListener("keyboardWillHide", () => {
    document.body.classList.remove("keyboard-open");
  });
}
