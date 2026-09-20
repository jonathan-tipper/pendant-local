import AppKit
import WebKit
import CryptoKit

final class LocalSessionDelegate: NSObject, URLSessionTaskDelegate {
    func urlSession(_ session: URLSession, task: URLSessionTask, willPerformHTTPRedirection response: HTTPURLResponse, newRequest request: URLRequest, completionHandler: @escaping (URLRequest?) -> Void) {
        completionHandler(nil)
    }
}

// This launcher never sends the local token until the service proves possession
// of it. Keep the origin fixed and never put credentials in a URL or log.
final class PendantApp: NSObject, NSApplicationDelegate, WKNavigationDelegate, WKUIDelegate, WKDownloadDelegate, NSWindowDelegate {
    var window: NSWindow!
    var web: WKWebView!
    var service: Process?
    var log: FileHandle?
    var token = ""
    var ready = false
    var quitting = false
    var checkingQuit = false
    var startupTimer: Timer?
    var healthTimer: Timer?
    var initialLogin = false
    var attempts = 0
    let session = URLSession(configuration: .ephemeral, delegate: LocalSessionDelegate(), delegateQueue: nil)
    let fm = FileManager.default
    var workspace: URL {
        if let path = Bundle.main.object(forInfoDictionaryKey: "PendantWorkspacePath") as? String { return URL(fileURLWithPath: path) }
        return fm.homeDirectoryForCurrentUser.appendingPathComponent("Library/Application Support/pendant-local-api")
    }
    var port: Int { (Bundle.main.object(forInfoDictionaryKey: "PendantServicePort") as? Int) ?? 8766 }
    var origin: String { "http://127.0.0.1:\(port)" }
    var executable: URL { Bundle.main.bundleURL.appendingPathComponent("Contents/MacOS/pendant-service") }
    var logURL: URL { workspace.appendingPathComponent("desktop-service.log") }

    func applicationDidFinishLaunching(_ notification: Notification) {
        makeMenu()
        let configuration = WKWebViewConfiguration()
        configuration.mediaTypesRequiringUserActionForPlayback = []
        web = WKWebView(frame: .zero, configuration: configuration)
        web.navigationDelegate = self
        web.uiDelegate = self
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 1200, height: 820), styleMask: [.titled, .closable, .miniaturizable, .resizable], backing: .buffered, defer: false)
        window.title = Bundle.main.object(forInfoDictionaryKey: "CFBundleDisplayName") as? String ?? "Pendant"
        window.minSize = NSSize(width: 720, height: 560)
        window.contentView = web
        window.delegate = self
        window.isReleasedWhenClosed = false
        window.setFrameAutosaveName("PendantMainWindow")
        window.center()
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        showMessage("Opening your workspace…", "Starting the local service. Your recordings stay on this Mac.")
        initialise()
    }

    func makeMenu() {
        let bar = NSMenu()
        let appItem = NSMenuItem(); bar.addItem(appItem)
        let appMenu = NSMenu(); appItem.submenu = appMenu
        appMenu.addItem(withTitle: "About Pendant", action: #selector(about), keyEquivalent: "")
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle: "Unlock Workspace", action: #selector(unlock), keyEquivalent: "")
        appMenu.addItem(withTitle: "Show Workspace Folder", action: #selector(showFolder), keyEquivalent: "")
        appMenu.addItem(withTitle: "Show Service Log", action: #selector(showLog), keyEquivalent: "")
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle: "Hide Pendant", action: #selector(NSApplication.hide(_:)), keyEquivalent: "h")
        appMenu.addItem(withTitle: "Quit Pendant", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        let editItem = NSMenuItem(); bar.addItem(editItem); let edit = NSMenu(title: "Edit"); editItem.submenu = edit
        for (title, action, key) in [("Undo", "undo:", "z"), ("Cut", "cut:", "x"), ("Copy", "copy:", "c"), ("Paste", "paste:", "v"), ("Select All", "selectAll:", "a")] {
            edit.addItem(withTitle: title, action: Selector(action), keyEquivalent: key)
        }
        let windowItem = NSMenuItem(); bar.addItem(windowItem); let menu = NSMenu(title: "Window"); windowItem.submenu = menu
        menu.addItem(withTitle: "Show Pendant", action: #selector(showWindow), keyEquivalent: "0")
        menu.addItem(withTitle: "Reload", action: #selector(reload), keyEquivalent: "r")
        menu.addItem(withTitle: "Close Window", action: #selector(NSWindow.performClose(_:)), keyEquivalent: "w")
        NSApp.mainMenu = bar
    }

    @objc func about() {
        NSApp.orderFrontStandardAboutPanel(options: [.applicationName: "Pendant", .applicationVersion: Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") ?? "", .credits: NSAttributedString(string: "Independent local workspace for your Limitless Pendant.\nRecordings, transcription and speaker analysis stay on your Mac.\nThird-party licences are included in the app’s Resources folder.")])
    }
    @objc func showFolder() { NSWorkspace.shared.open(workspace) }
    @objc func unlock() {
        guard ready else { return }
        identity { valid, _ in
            if valid { self.openWorkspace(); self.showWindow() }
            else { self.fail("The local service could not be verified. Reopen Pendant to reconnect.") }
        }
    }
    @objc func showLog() { NSWorkspace.shared.activateFileViewerSelecting([logURL]) }
    @objc func showWindow() { window.makeKeyAndOrderFront(nil); NSApp.activate(ignoringOtherApps: true) }
    @objc func reload() { if ready { web.reload() } }
    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool { showWindow(); return true }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { false }

    func showMessage(_ title: String, _ detail: String) {
        // Only fixed application strings go into this HTML, never errors/user data.
        web.loadHTMLString("<html><body style='background:#10151c;color:#edf3f7;font:18px -apple-system;padding:80px'><h1>\(title)</h1><p>\(detail)</p></body></html>", baseURL: nil)
    }
    func fail(_ message: String) {
        startupTimer?.invalidate(); healthTimer?.invalidate(); ready = false
        let alert = NSAlert(); alert.messageText = "Pendant couldn’t open the workspace"; alert.informativeText = message
        alert.addButton(withTitle: "Show log"); alert.addButton(withTitle: "Quit")
        if alert.runModal() == .alertFirstButtonReturn { showLog() }
        quitting = true
        if let process = service, process.isRunning { process.terminate() } else { NSApp.terminate(nil) }
    }
    func process(arguments: [String]) -> Process {
        let p = Process(); p.executableURL = executable; p.arguments = ["--data-dir", workspace.path] + arguments
        var env = ProcessInfo.processInfo.environment
        // Finder and development shells must resolve to the same explicit workspace.
        for key in Array(env.keys) where key.hasPrefix("PYTHON") || key.hasPrefix("PENDANT_") || key.hasPrefix("DYLD_") { env.removeValue(forKey: key) }
        env["TOKENIZERS_PARALLELISM"] = "false"
        p.environment = env; p.currentDirectoryURL = workspace; p.standardOutput = log; p.standardError = log
        return p
    }
    func initialise() {
        do {
            try fm.createDirectory(at: workspace, withIntermediateDirectories: true, attributes: [.posixPermissions: 0o700])
            if let size = try? fm.attributesOfItem(atPath: logURL.path)[.size] as? NSNumber, size.intValue > 5_000_000 {
                let previous = workspace.appendingPathComponent("desktop-service.previous.log")
                if fm.fileExists(atPath: previous.path) { try fm.removeItem(at: previous) }
                try fm.moveItem(at: logURL, to: previous)
            }
            if !fm.fileExists(atPath: logURL.path) { fm.createFile(atPath: logURL.path, contents: nil, attributes: [.posixPermissions: 0o600]) }
            log = try FileHandle(forWritingTo: logURL); log?.seekToEndOfFile()
            let initProcess = process(arguments: ["doctor"])
            initProcess.terminationHandler = { p in DispatchQueue.main.async {
                guard p.terminationStatus == 0 else { self.fail("The bundled service could not initialise. The service log has the details."); return }
                do {
                    let config = try JSONSerialization.jsonObject(with: Data(contentsOf: self.workspace.appendingPathComponent("config.json"))) as? [String: Any]
                    guard let value = config?["api_token"] as? String, value.count >= 20 else { throw NSError(domain: "Pendant", code: 1) }
                    self.token = value; self.findService()
                } catch { self.fail("The workspace configuration could not be read. Your recordings have not been removed.") }
            }}
            try initProcess.run()
        } catch { fail("The bundled service could not start. Check that the app can read and write its workspace folder.") }
    }

    func request(_ path: String, authenticated: Bool = false, completion: @escaping (Data?, HTTPURLResponse?, Error?) -> Void) {
        var request = URLRequest(url: URL(string: origin + path)!, cachePolicy: .reloadIgnoringLocalCacheData, timeoutInterval: 3)
        if authenticated { request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization") }
        session.dataTask(with: request) { data, response, error in DispatchQueue.main.async { completion(data, response as? HTTPURLResponse, error) } }.resume()
    }
    func identity(_ completion: @escaping (Bool, Bool) -> Void) {
        let challenge = UUID().uuidString.replacingOccurrences(of: "-", with: "").lowercased() + UUID().uuidString.replacingOccurrences(of: "-", with: "").lowercased()
        request("/desktop/identity?challenge=\(challenge)") { data, response, error in
            guard let data = data, response?.statusCode == 200,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let version = json["version"] as? String, let proof = json["proof"] as? String else { completion(false, response != nil); return }
            let message = Data("pendant-desktop-v1:\(challenge):\(version)".utf8)
            let expected = HMAC<SHA256>.authenticationCode(for: message, using: SymmetricKey(data: Data(self.token.utf8))).map { String(format: "%02x", $0) }.joined()
            let compatible = version == Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String
            completion(proof == expected && compatible, true)
        }
    }
    func findService() {
        identity { valid, occupied in
            if valid { self.openWorkspace(); return }
            if occupied { self.fail("Port \(self.port) is used by a different or older service. Finish any work there and stop that service, then open Pendant again. No other process has been stopped."); return }
            do {
                let p = self.process(arguments: ["serve", "--port", String(self.port)])
                self.service = p
                p.terminationHandler = { _ in DispatchQueue.main.async {
                    if self.quitting { NSApp.reply(toApplicationShouldTerminate: true); NSApp.terminate(nil) }
                    else { self.fail("The local service stopped. Your recordings remain in the workspace. Check the service log, then reopen Pendant.") }
                }}
                try p.run()
                self.startupTimer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { _ in self.waitForService() }
            } catch { self.fail("The bundled local service could not be launched.") }
        }
    }
    var probing = false
    func waitForService() {
        if probing { return }; attempts += 1
        if attempts > 180 { fail("The service is taking too long to open the workspace. Check its log before trying again."); return }
        probing = true
        identity { valid, _ in
            self.probing = false
            if valid { self.startupTimer?.invalidate(); self.openWorkspace() }
        }
    }
    func openWorkspace() {
        ready = true; initialLogin = true
        let encodedToken = String(data: try! JSONSerialization.data(withJSONObject: [token]), encoding: .utf8)!
        let js = "if (location.origin === '\(origin)') { sessionStorage.setItem('pendant_token', \(encodedToken)[0]); }"
        web.configuration.userContentController.addUserScript(WKUserScript(source: js, injectionTime: .atDocumentStart, forMainFrameOnly: true))
        web.load(URLRequest(url: URL(string: origin + "/ui/")!))
    }
    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        if let url = webView.url, local(url) {
            webView.evaluateJavaScript("""
                (() => {
                    const form = document.getElementById('login-form');
                    if (!form || document.getElementById('native-unlock-hint')) return;
                    form.hidden = true;
                    const hint = document.createElement('p');
                    hint.id = 'native-unlock-hint'; hint.className = 'field-help';
                    hint.textContent = 'Choose Pendant → Unlock Workspace from the Mac menu bar to open your local workspace.';
                    form.before(hint);
                })();
                """, completionHandler: nil)
        }
        if initialLogin && webView.url?.host == "127.0.0.1" {
            web.configuration.userContentController.removeAllUserScripts(); initialLogin = false
        }
    }
    func local(_ url: URL) -> Bool {
        url.scheme == "http" && url.host == "127.0.0.1" && url.port == port && url.user == nil && url.password == nil
    }
    func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        guard let url = action.request.url else { decisionHandler(.cancel); return }
        if url.absoluteString == "about:blank" { decisionHandler(.allow); return }
        if local(url) || url.absoluteString.hasPrefix("blob:\(origin)/") {
            if action.shouldPerformDownload { decisionHandler(.download) } else { decisionHandler(.allow) }; return
        }
        decisionHandler(.cancel)
        if action.navigationType == .linkActivated, ["http", "https"].contains(url.scheme ?? "") { NSWorkspace.shared.open(url) }
    }
    func webView(_ webView: WKWebView, createWebViewWith configuration: WKWebViewConfiguration, for action: WKNavigationAction, windowFeatures: WKWindowFeatures) -> WKWebView? {
        if let url = action.request.url {
            if local(url) { web.load(action.request) }
            else if action.navigationType == .linkActivated, ["http", "https"].contains(url.scheme ?? "") { NSWorkspace.shared.open(url) }
        }
        return nil
    }
    func webView(_ webView: WKWebView, decidePolicyFor response: WKNavigationResponse, decisionHandler: @escaping (WKNavigationResponsePolicy) -> Void) {
        decisionHandler(response.canShowMIMEType ? .allow : .download)
    }
    func webView(_ webView: WKWebView, navigationAction: WKNavigationAction, didBecome download: WKDownload) { download.delegate = self }
    func webView(_ webView: WKWebView, navigationResponse: WKNavigationResponse, didBecome download: WKDownload) { download.delegate = self }
    func download(_ download: WKDownload, decideDestinationUsing response: URLResponse, suggestedFilename: String, completionHandler: @escaping (URL?) -> Void) {
        let panel = NSSavePanel(); panel.nameFieldStringValue = URL(fileURLWithPath: suggestedFilename).lastPathComponent
        panel.beginSheetModal(for: window) { result in completionHandler(result == .OK ? panel.url : nil) }
    }
    func download(_ download: WKDownload, didFailWithError error: Error, resumeData: Data?) {
        let alert = NSAlert(); alert.messageText = "The export wasn’t saved"; alert.informativeText = "Try exporting again and choose a writable folder."; alert.beginSheetModal(for: window)
    }
    func webView(_ webView: WKWebView, runOpenPanelWith parameters: WKOpenPanelParameters, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping ([URL]?) -> Void) {
        let panel = NSOpenPanel(); panel.canChooseDirectories = false; panel.allowsMultipleSelection = parameters.allowsMultipleSelection
        panel.beginSheetModal(for: window) { result in completionHandler(result == .OK ? panel.urls : nil) }
    }
    func webView(_ webView: WKWebView, runJavaScriptConfirmPanelWithMessage message: String, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (Bool) -> Void) {
        let alert = NSAlert(); alert.messageText = message; alert.addButton(withTitle: "Continue"); alert.addButton(withTitle: "Cancel")
        alert.beginSheetModal(for: window) { completionHandler($0 == .alertFirstButtonReturn) }
    }
    func webView(_ webView: WKWebView, runJavaScriptAlertPanelWithMessage message: String, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping () -> Void) {
        let alert = NSAlert(); alert.messageText = message
        alert.beginSheetModal(for: window) { _ in completionHandler() }
    }
    func webViewWebContentProcessDidTerminate(_ webView: WKWebView) { if ready { web.reload() } }

    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        if quitting { return service?.isRunning == true ? .terminateLater : .terminateNow }
        guard let p = service, p.isRunning else { return .terminateNow }
        if !ready { quitting = true; p.terminate(); return .terminateLater }
        if checkingQuit { return .terminateLater }; checkingQuit = true
        request("/v1/desktop/status", authenticated: true) { data, response, _ in
            self.checkingQuit = false
            let state = data.flatMap { try? JSONSerialization.jsonObject(with: $0) as? [String: Any] }
            guard response?.statusCode == 200, state?["busy"] as? Bool == false else {
                let alert = NSAlert(); alert.messageText = "Keep Pendant open while work finishes"
                alert.informativeText = "A transfer, transcription or model download may still be running. Wait for it to finish, or cancel it in the workspace, then quit. Closing this window keeps the app running."
                alert.addButton(withTitle: "Keep running"); alert.runModal(); NSApp.reply(toApplicationShouldTerminate: false); return
            }
            self.quitting = true
            self.showMessage("Closing the workspace…", "Finishing local work and saving state.")
            p.terminate()
        }
        return .terminateLater
    }
}

let app = NSApplication.shared
let delegate = PendantApp()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.run()
