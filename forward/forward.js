/* peterstieg.github.io – types two shell lines, then forwards to the same path on peterstieg.com.
   Enter or a click skips the wait, Esc or Ctrl+C stops it. */
(() => {
  window.fw = true;                       // tells the failsafe in the page head that this file arrived
  const root = document.documentElement;
  root.classList.add("js");
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Where to: same path, query and hash on peterstieg.com; old /site/ links lose that prefix. */
  const path = location.pathname.replace(/^\/site(?=\/|$)/, "");
  const target = "https://peterstieg.com" + path + location.search + location.hash;

  const term = document.querySelector(".term");
  const go = term.querySelector(".go");
  const [first, output, second] = term.querySelectorAll(".line");
  go.querySelector("a").href = target;

  // a deep link shows its path in the cd line – short paths only, and as text, never as HTML
  if (path.length > 1 && path.length <= 32) second.querySelector(".cmd").textContent = "cd peterstieg.com" + path;

  const cursor = document.createElement("span");
  cursor.className = "cursor";

  let state = "playing";                  // playing → leaving | stopped
  let timer = 0;
  const wait = (ms) => new Promise((done) => { timer = setTimeout(done, ms); });
  const show = (line) => line.classList.add("on");
  const prompt = (line) => { line.querySelector(".cmd").append(cursor); show(line); };  // the cursor moves here

  const leave = () => {
    if (state === "leaving") return;
    state = "leaving";
    clearTimeout(timer);
    location.replace(target);             // replace: the forward page does not stay in the back history
  };

  /* ---------- The scene: command, output, command – then off to peterstieg.com. */
  const type = async (text) => {        // into the line that holds the cursor
    for (const ch of text) {
      if (state !== "playing") return;
      cursor.before(ch);
      await wait(12 + Math.random() * 18);  // 12–30 ms per key: fast, but not mechanical
    }
  };

  const play = async () => {
    if (reduce) {                         // no typing: the finished screen, a moment to read it, go
      show(first);
      show(output);
      prompt(second);
      await wait(1200);
    } else {
      const text1 = first.querySelector(".cmd").textContent;
      const text2 = second.querySelector(".cmd").textContent;
      first.querySelector(".cmd").textContent = "";
      second.querySelector(".cmd").textContent = "";
      prompt(first);
      // type once the mono font is there (600 ms at most), so no line changes width mid-word
      await Promise.race([document.fonts && document.fonts.ready, wait(600)]);
      await wait(200);
      await type(text1);
      await wait(180);                    // "Enter"
      if (state !== "playing") return;
      show(output);
      prompt(second);
      await wait(450);
      await type(text2);
      await wait(300);
    }
    if (state === "playing") leave();
  };

  /* ---------- ^C: stop like a terminal – "^C" at the cursor, a fresh prompt, the link becomes visible. */
  const stop = () => {
    if (state !== "playing") return;
    state = "stopped";
    clearTimeout(timer);
    cursor.before("^C");
    term.querySelectorAll(".line:not(.on)").forEach((l) => l.remove());
    const fresh = first.cloneNode(false); // an empty <p class="line on" aria-hidden="true">
    fresh.innerHTML = '<span class="caret">&gt;_</span><span class="cmd"></span>';
    go.before(fresh);
    prompt(fresh);
    cursor.classList.add("blink");
    go.classList.add("on");
  };

  document.addEventListener("keydown", (e) => {
    const key = e.key || "";              // some synthetic events (autofill) carry no key
    const ctrlC = e.ctrlKey && !e.altKey && key.toLowerCase() === "c" && !String(getSelection());
    if (key === "Escape" || ctrlC) stop();
    else if (key === "Enter" && !e.target.closest("a")) leave();
  });
  document.addEventListener("click", (e) => {
    if (state === "playing" && !e.target.closest("a")) leave();
  });

  play();
})();
