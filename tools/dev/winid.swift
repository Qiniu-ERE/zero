import CoreGraphics
import Foundation
// 打印某个进程名的最大窗口 ID（用于 screencapture -l 只截游戏窗口）
let owner = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "gdspxrt"
let list = CGWindowListCopyWindowInfo([.optionAll], kCGNullWindowID) as! [[String: Any]]
var best: (Int, Double) = (0, 0)
for w in list {
    guard let name = w[kCGWindowOwnerName as String] as? String, name.contains(owner),
          let id = w[kCGWindowNumber as String] as? Int,
          let b = w[kCGWindowBounds as String] as? [String: Double] else { continue }
    let area = (b["Width"] ?? 0) * (b["Height"] ?? 0)
    if area > best.1 { best = (id, area) }
}
if best.0 != 0 { print(best.0) } else { exit(1) }
