// 注意：live2d_path 参数应使用绝对路径 看看有没有改成功
const core_js = "https://fastly.jsdelivr.net/gh/stevenjoezhang/live2d-widget@latest/live2d.min.js";
function loadExternalResource(url, type) {
  return new Promise((resolve, reject) => {
    let tag
    if (type === "css") { tag = document.createElement("link"); tag.rel = "stylesheet"; tag.href = url }
    else if (type === "js") { tag = document.createElement("script"); tag.src = url }
    if (tag) { tag.onload = () => resolve(url); tag.onerror = () => reject(url); document.head.appendChild(tag) }
  })
}

if (screen.width >= 768) {
  Promise.all([
    loadExternalResource(core_js, "js"),
    loadExternalResource("/live2d-widget/waifu-config.js", "js"),
    loadExternalResource("/live2d-widget/waifu-tips.js", "js")
  ]).then(() => {
    initWidget({ waifuPath: "/live2d-widget/waifu-tips.json", apiPath: "https://api.zsq.im/live2d" })
  })
}

console.log("[Live2D] autoload (no default CSS) initialized")
