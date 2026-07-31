// Reloading/closing the tab while a request is still in flight aborts it outright - the
// backend never receives it, so the same still-open question (or a lost "start interview")
// silently reappears with no error. Most browsers ignore the custom message text and just
// show their own generic "leave site?" prompt, but setting returnValue is what actually
// triggers that prompt at all.
export function warnBeforeUnload(event) {
  event.preventDefault();
  event.returnValue = "";
}
