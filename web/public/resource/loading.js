/**
 * 初始化加载效果的svg格式logo
 * @param {string} id - 元素id
 */
 function initSvgLogo(id) {
  const svgStr = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 140" fill="none"><path fill-rule="evenodd" d="M30 105 L30 75 Q30 55 55 55 L95 55 L110 30 Q115 22 125 22 L155 22 Q165 22 170 30 L185 55 L210 55 Q215 55 215 60 L215 105 Z M118 32 L150 32 L162 50 L106 50 Z" fill="#0EA371"></path><circle cx="75" cy="108" r="16" fill="#0EA371"></circle><circle cx="170" cy="108" r="16" fill="#0EA371"></circle></svg>`
  const appEl = document.querySelector(id)
  const div = document.createElement('div')
  div.innerHTML = svgStr
  if (appEl) {
    appEl.appendChild(div)
  }
}

function addThemeColorCssVars() {
  const key = '__THEME_COLOR__'
  const defaultColor = '#0EA371'
  const themeColor = window.localStorage.getItem(key) || defaultColor
  const cssVars = `--primary-color: ${themeColor}`
  document.documentElement.style.cssText = cssVars
}

addThemeColorCssVars()

initSvgLogo('#loadingLogo')
