"use strict";

// Each tab group is independent and supports the standard keyboard controls.
document.querySelectorAll('[role="tablist"]').forEach((group) => {
  const tabs = [...group.querySelectorAll('[role="tab"]')];
  const activate = (selected, moveFocus = false) => {
    tabs.forEach((tab) => {
      const active = tab === selected;
      tab.setAttribute("aria-selected", String(active));
      tab.tabIndex = active ? 0 : -1;
      tab.classList.toggle("active", active);
      document.getElementById(tab.getAttribute("aria-controls")).hidden = !active;
    });
    if (moveFocus) selected.focus();
  };
  tabs.forEach((tab, index) => {
    tab.addEventListener("click", () => activate(tab));
    tab.addEventListener("keydown", (event) => {
      let next;
      if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
      if (event.key === "ArrowLeft") next = (index - 1 + tabs.length) % tabs.length;
      if (event.key === "Home") next = 0;
      if (event.key === "End") next = tabs.length - 1;
      if (next !== undefined) {
        event.preventDefault();
        activate(tabs[next], true);
      }
    });
  });
});

const copyButton = document.getElementById("copy-bibtex");
const copyStatus = document.getElementById("copy-status");
copyButton.addEventListener("click", async () => {
  const code = document.getElementById("bibtex");
  try {
    await navigator.clipboard.writeText(code.textContent);
    copyButton.textContent = "Copied!";
    copyStatus.textContent = "Citation copied to clipboard.";
    window.setTimeout(() => { copyButton.textContent = "Copy"; }, 2000);
  } catch {
    // A selectable fallback also works when clipboard permissions are denied.
    const range = document.createRange();
    range.selectNodeContents(code);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    copyStatus.textContent = "Citation selected. Press Ctrl+C (or Command+C) to copy.";
  }
});

// Mark the section nearest the top of the viewport in the desktop contents.
const sectionLinks = [...document.querySelectorAll('.toc a[href^="#"]')]
  .filter((link) => link.hash !== "#top");
let scrollPending = false;
const updateContents = () => {
  let current = sectionLinks[0];
  sectionLinks.forEach((link) => {
    if (document.querySelector(link.hash).getBoundingClientRect().top <= 170) current = link;
  });
  sectionLinks.forEach((link) => {
    if (link === current) link.setAttribute("aria-current", "location");
    else link.removeAttribute("aria-current");
  });
  scrollPending = false;
};
window.addEventListener("scroll", () => {
  if (!scrollPending) {
    scrollPending = true;
    window.requestAnimationFrame(updateContents);
  }
}, { passive: true });
updateContents();

// Leave playback under the visitor's control and pause when the tab is hidden.
document.addEventListener("visibilitychange", () => {
  if (document.hidden) document.getElementById("navigation-video").pause();
});
