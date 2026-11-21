// Screenshot a local HTML page in WebKit (Safari's engine).
// usage: swift webkit_shot.swift PAGE.html READ_ACCESS_DIR OUT.png [WIDTH HEIGHT]
import AppKit
import WebKit

let args = CommandLine.arguments
let page = URL(fileURLWithPath: args[1])
let root = URL(fileURLWithPath: args[2])
let out = URL(fileURLWithPath: args[3])
let w = args.count > 4 ? Double(args[4])! : 1300
let h = args.count > 5 ? Double(args[5])! : 1500

class Delegate: NSObject, WKNavigationDelegate {
    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        // give web fonts a moment to load and lay out
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
            webView.evaluateJavaScript("JSON.stringify({fonts: [...document.fonts].map(f => f.family + ':' + f.status), ua: navigator.userAgent, widths: [...document.querySelectorAll('.big')].map(e => e.getBoundingClientRect().height)})") { result, _ in
                print(result ?? "no result")
                let config = WKSnapshotConfiguration()
                webView.takeSnapshot(with: config) { image, error in
                    if let image = image, let tiff = image.tiffRepresentation, let rep = NSBitmapImageRep(data: tiff),
                       let png = rep.representation(using: .png, properties: [:]) {
                        try? png.write(to: out)
                        print("wrote", out.path)
                    } else {
                        print("snapshot failed", error ?? "")
                    }
                    exit(0)
                }
            }
        }
    }
    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) { print("failed", error); exit(1) }
}

let app = NSApplication.shared
app.setActivationPolicy(.prohibited)
let web = WKWebView(frame: NSRect(x: 0, y: 0, width: w, height: h))
let delegate = Delegate()
web.navigationDelegate = delegate
web.loadFileURL(page, allowingReadAccessTo: root)
DispatchQueue.main.asyncAfter(deadline: .now() + 40) { print("timeout"); exit(2) }
app.run()
