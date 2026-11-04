// Manage keyboard input sources through Carbon, rather than overwriting HIToolbox preferences.
import Carbon
import Foundation

struct Config: Decodable {
    let enabled: [String]
    let selected: String
}
func property(_ source: TISInputSource, _ key: CFString) -> CFTypeRef? {
    guard let pointer = TISGetInputSourceProperty(source, key) else { return nil }
    return Unmanaged<CFTypeRef>.fromOpaque(pointer).takeUnretainedValue()
}
func id(_ source: TISInputSource) -> String {
    property(source, kTISPropertyInputSourceID) as? String ?? ""
}
func flag(_ source: TISInputSource, _ key: CFString) -> Bool {
    (property(source, key) as? NSNumber)?.boolValue ?? false
}
func sources() -> [TISInputSource] {
    TISCreateInputSourceList(nil, true).takeRetainedValue() as! [TISInputSource]
}
func keyboards() -> [TISInputSource] {
    sources().filter {
        property($0, kTISPropertyInputSourceCategory) as? String == kTISCategoryKeyboardInputSource as String
        && flag($0, kTISPropertyInputSourceIsSelectCapable)
    }
}
// macOS can report a child mode as enabled while its entire input method is disabled.
func enabled(_ source: TISInputSource) -> Bool {
    guard flag(source, kTISPropertyInputSourceIsEnabled) else { return false }
    let bundle = property(source, kTISPropertyBundleID) as? String
    if let bundle, let parent = sources().first(where: {
        property($0, kTISPropertyBundleID) as? String == bundle
        && property($0, kTISPropertyInputSourceType) as? String == kTISTypeKeyboardInputMethodModeEnabled as String
    }) { return flag(parent, kTISPropertyInputSourceIsEnabled) }
    return true
}
func require(_ status: OSStatus, _ action: String) throws {
    if status != noErr {
        throw NSError(domain: "InputSources", code: Int(status), userInfo: [NSLocalizedDescriptionKey:
            "\(action) failed (\(status)). Log out and back in after installing Google IME, then retry."])
    }
}

do {
    let args = Array(CommandLine.arguments.dropFirst())
    guard let configPath = args.first else { throw NSError(domain: "InputSources", code: 1,
        userInfo: [NSLocalizedDescriptionKey: "Usage: swift input-sources.swift config.json [--check]"]) }
    let config = try JSONDecoder().decode(Config.self, from: Data(contentsOf: URL(fileURLWithPath: configPath)))
    let wanted = Set(config.enabled)
    guard wanted.contains(config.selected), wanted.contains("com.apple.keylayout.ABC") else {
        throw NSError(domain: "InputSources", code: 1, userInfo: [NSLocalizedDescriptionKey: "Keep ABC enabled and select an enabled source."])
    }
    let check = args.contains("--check")
    if !check && wanted.contains(where: { $0.hasPrefix("com.google.inputmethod.Japanese") }) {
        let app = URL(fileURLWithPath: "/Library/Input Methods/GoogleJapaneseInput.app")
        guard FileManager.default.fileExists(atPath: app.path) else {
            throw NSError(domain: "InputSources", code: 1, userInfo: [NSLocalizedDescriptionKey: "Install google-japanese-ime with Homebrew first."])
        }
        try require(TISRegisterInputSource(app as CFURL), "Register Google IME")
    }
    // Validate every requested source before changing anything.
    let available = keyboards()
    for name in wanted where !available.contains(where: { id($0) == name }) {
        throw NSError(domain: "InputSources", code: 1, userInfo: [NSLocalizedDescriptionKey: "Missing input source: \(name). Log out and back in after installing IME."])
    }
    if !check {
        // Enable replacements and select one before disabling existing sources.
        for source in available where wanted.contains(id(source)) && !enabled(source) {
            try require(TISEnableInputSource(source), "Enable \(id(source))")
        }
        guard let selected = keyboards().first(where: { id($0) == config.selected }) else { fatalError("Source disappeared") }
        try require(TISSelectInputSource(selected), "Select \(config.selected)")
        // Some built-in modes (notably Kotoeri Roman) remain enabled after
        // disabling the child. Disable an unwanted input method at its parent.
        let wantedBundles = Set(available.filter { wanted.contains(id($0)) }.compactMap {
            property($0, kTISPropertyBundleID) as? String
        })
        for parent in sources() where
            property(parent, kTISPropertyInputSourceType) as? String == kTISTypeKeyboardInputMethodModeEnabled as String
            && flag(parent, kTISPropertyInputSourceIsEnabled) {
            if let bundle = property(parent, kTISPropertyBundleID) as? String,
               !wantedBundles.contains(bundle) {
                try require(TISDisableInputSource(parent), "Disable input method \(id(parent))")
            }
        }
        for source in keyboards() where !wanted.contains(id(source)) && enabled(source) {
            try require(TISDisableInputSource(source), "Disable \(id(source))")
        }
    }
    let actual = Set(keyboards().filter { enabled($0) }.map(id))
    let current = id(TISCopyCurrentKeyboardInputSource().takeRetainedValue())
    guard actual == wanted, current == config.selected else {
        throw NSError(domain: "InputSources", code: 1, userInfo: [NSLocalizedDescriptionKey:
            "Input sources differ: enabled=\(actual.sorted()), selected=\(current). Retry from Terminal in your logged-in desktop session."])
    }
    print("Input sources match: ABC + Hiragana (Google); selected: Hiragana (Google)")
} catch {
    fputs("\(error.localizedDescription)\n", stderr)
    exit(1)
}
