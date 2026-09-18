/**
 * electron-builder afterPack hook for OpenLore Studio.
 *
 * Ensures proper code signing and resource sealing for macOS builds:
 * - If formal Apple Developer ID credentials (CSC_LINK or CSC_NAME) are NOT provided,
 *   performs deep ad-hoc signing (`codesign --force --deep -s -`) on the packaged .app bundle.
 *   This eliminates the "code has no resources but signature indicates they must be present"
 *   integrity discrepancy that triggers Gatekeeper "file is damaged" alerts.
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

module.exports = async function (context) {
  if (context.electronPlatformName !== 'darwin') {
    return;
  }

  const appName = context.packager.appInfo.productFilename;
  const appPath = path.join(context.appOutDir, `${appName}.app`);

  if (!fs.existsSync(appPath)) {
    console.warn(`[afterPack] Target app bundle does not exist at: ${appPath}`);
    return;
  }

  const hasCert = Boolean(process.env.CSC_LINK || process.env.CSC_NAME);
  if (!hasCert) {
    console.log(`[afterPack] Re-signing macOS bundle ad-hoc to seal resources: ${appName}.app`);
    try {
      execSync(`codesign --force --deep -s - "${appPath}"`, { stdio: 'inherit' });
      console.log(`[afterPack] ✅ Successfully ad-hoc signed and sealed: ${appName}.app`);
    } catch (err) {
      console.warn(`[afterPack] ⚠️ Failed to ad-hoc codesign ${appPath}:`, err.message);
    }
  } else {
    console.log(`[afterPack] Apple Developer ID certificate detected; relying on standard code signing pipeline.`);
  }
};
