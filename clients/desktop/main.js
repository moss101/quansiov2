// Quansio V9 desktop workbench (UX-001): Electron shell around the canonical
// web projection. The shell adds windowing only — all workbench behavior is
// the canonical command/event projection in clients/web, so desktop and web
// clients converge identically by construction.
const { app, BrowserWindow } = require("electron");
const path = require("path");

function createWindow() {
  const window = new BrowserWindow({
    width: 1280,
    height: 820,
    title: "Quansio Workbench",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });
  window.loadFile(path.join(__dirname, "..", "web", "index.html"));
}

app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
