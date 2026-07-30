import { useEffect, useState } from "react";
import Typography from "@mui/material/Typography";

const CHAR_DELAY_MS = 12;

export default function TypewriterText({ text, variant = "body1" }) {
  const [shown, setShown] = useState("");

  useEffect(() => {
    setShown("");
    if (!text) return undefined;

    let index = 0;
    const interval = setInterval(() => {
      index += 1;
      setShown(text.slice(0, index));
      if (index >= text.length) {
        clearInterval(interval);
      }
    }, CHAR_DELAY_MS);

    return () => clearInterval(interval);
  }, [text]);

  const done = shown.length === (text || "").length;

  return (
    <Typography variant={variant}>
      {shown}
      {!done && <span className="typewriter-cursor">&nbsp;</span>}
    </Typography>
  );
}
