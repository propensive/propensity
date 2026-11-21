// Shape and draw text with CoreText (the engine Safari uses) to confirm the font works there.
// usage: swift coretext.swift FONT OUT.png SIZE LINE [LINE ...]
import CoreGraphics
import CoreText
import Foundation
import ImageIO

let args = CommandLine.arguments
let url = URL(fileURLWithPath: args[1])
let size = CGFloat(Double(args[3])!)
guard let descs = CTFontManagerCreateFontDescriptorsFromURL(url as CFURL) as? [CTFontDescriptor], let desc = descs.first else {
    print("CoreText could not read the font"); exit(1)
}
let font = CTFontCreateWithFontDescriptor(desc, size, nil)
print("postscript name:", CTFontCopyPostScriptName(font), "| glyphs:", CTFontGetGlyphCount(font))
let lines = Array(args[4...])
let width = 2400, lineH = Int(size * 1.5)
let height = lineH * lines.count + Int(size)
let ctx = CGContext(data: nil, width: width, height: height, bitsPerComponent: 8, bytesPerRow: 0,
                    space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
ctx.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
ctx.fill(CGRect(x: 0, y: 0, width: width, height: height))
for (i, text) in lines.enumerated() {
    let attr = NSAttributedString(string: text, attributes: [kCTFontAttributeName as NSAttributedString.Key: font,
        kCTForegroundColorAttributeName as NSAttributedString.Key: CGColor(red: 0, green: 0, blue: 0, alpha: 1)])
    let line = CTLineCreateWithAttributedString(attr)
    let runs = CTLineGetGlyphRuns(line) as! [CTRun]
    var summary: [String] = []
    var zero = 0
    for run in runs {
        let attrs = CTRunGetAttributes(run) as NSDictionary
        let runFont = attrs[kCTFontAttributeName] as! CTFont
        let n = CTRunGetGlyphCount(run)
        var glyphs = [CGGlyph](repeating: 0, count: n)
        CTRunGetGlyphs(run, CFRange(location: 0, length: n), &glyphs)
        zero += glyphs.filter { $0 == 0 }.count
        summary.append("\(CTFontCopyPostScriptName(runFont)) x\(n)")
    }
    print("line \(i): chars \(text.unicodeScalars.count), runs [\(summary.joined(separator: ", "))], missing glyphs \(zero), width \(Int(CTLineGetTypographicBounds(line, nil, nil, nil)))")
    ctx.textPosition = CGPoint(x: 30, y: CGFloat(height - lineH * (i + 1)))
    CTLineDraw(line, ctx)
}
let dest = CGImageDestinationCreateWithURL(URL(fileURLWithPath: args[2]) as CFURL, "public.png" as CFString, 1, nil)!
CGImageDestinationAddImage(dest, ctx.makeImage()!, nil)
CGImageDestinationFinalize(dest)
