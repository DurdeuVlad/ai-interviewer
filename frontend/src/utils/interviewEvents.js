// Sidebar refetches its conversation list on route change (covers navigating to a new/different
// interview), but an interview can also complete in place with no navigation now that the summary
// renders inline instead of routing to /summary. This tiny window event bridges that one gap
// without a global store - just a signal to refetch, no state carried.
const EVENT_NAME = "interviews-changed";

export function notifyInterviewsChanged() {
  window.dispatchEvent(new Event(EVENT_NAME));
}

export function onInterviewsChanged(handler) {
  window.addEventListener(EVENT_NAME, handler);
  return () => window.removeEventListener(EVENT_NAME, handler);
}
