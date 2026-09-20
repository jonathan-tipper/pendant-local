import AppKit
let output = URL(fileURLWithPath: CommandLine.arguments[1])
try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
for size in [16, 32, 128, 256, 512] {
    for scale in [1, 2] {
        let pixels = size * scale
        let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: pixels, pixelsHigh: pixels, bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
        NSGraphicsContext.saveGraphicsState(); NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
        let factor = CGFloat(pixels) / 1024
        let transform = NSAffineTransform(); transform.scale(by: factor); transform.concat()
        NSColor(red: 0.60, green: 0.89, blue: 0.87, alpha: 1).setFill()
        NSBezierPath(roundedRect: NSRect(x: 62, y: 62, width: 900, height: 900), xRadius: 208, yRadius: 208).fill()
        let font = NSFont(name: "Georgia-BoldItalic", size: 790) ?? NSFont.boldSystemFont(ofSize: 790)
        let attrs: [NSAttributedString.Key: Any] = [.font: font, .foregroundColor: NSColor(red: 0.055, green: 0.105, blue: 0.13, alpha: 1)]
        let text = NSAttributedString(string: "p", attributes: attrs)
        text.draw(at: NSPoint(x: (1024 - text.size().width) / 2 - 12, y: 110))
        NSGraphicsContext.restoreGraphicsState()
        let name = "icon_\(size)x\(size)\(scale == 2 ? "@2x" : "").png"
        try rep.representation(using: .png, properties: [:])!.write(to: output.appendingPathComponent(name))
    }
}
