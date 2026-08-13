"use client";

import { FormEvent, useState } from "react";
import { supabase } from "@/lib/supabase";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMessage("");

    const response =
      mode === "register"
        ? await supabase.auth.signUp({ email, password })
        : await supabase.auth.signInWithPassword({ email, password });

    setBusy(false);

    if (response.error) {
      setMessage(response.error.message);
      return;
    }

    if (mode === "register" && !response.data.session) {
      setMessage("Registration successful. Check your email if confirmation is enabled.");
      return;
    }

    router.push("/analyze");
    router.refresh();
  }

  return (
    <section className="card" style={{ maxWidth: 620, margin: "0 auto" }}>
      <h1>{mode === "login" ? "Sign in" : "Create account"}</h1>
      <p className="muted">Use Supabase Auth to access your research workspace.</p>

      <form className="form" onSubmit={submit}>
        <label>
          Email
          <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>

        <label>
          Password
          <input type="password" minLength={8} required value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>

        {message && <div className={message.toLowerCase().includes("successful") ? "warning" : "error"}>{message}</div>}

        <button className="button primary" disabled={busy}>
          {busy ? "Please wait..." : mode === "login" ? "Sign in" : "Register"}
        </button>
      </form>

      <button
        className="button"
        style={{ marginTop: 12 }}
        onClick={() => {
          setMode(mode === "login" ? "register" : "login");
          setMessage("");
        }}
      >
        {mode === "login" ? "Need an account?" : "Already registered?"}
      </button>
    </section>
  );
}
