"use client";

import React, { useEffect, useRef } from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

interface HeroSectionProps {
  kicker?: string;
  title: React.ReactNode;
  subtitle: string;
  primaryCta?: { label: string; href: string };
  secondaryCta?: { label: string; href: string };
}

export default function HeroSection({
  kicker,
  title,
  subtitle,
  primaryCta = { label: "Get started", href: "/pricing" },
  secondaryCta = { label: "Documentation", href: "/docs" },
}: HeroSectionProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const setSize = () => {
      const parent = canvas.parentElement;
      if (!parent) return;
      canvas.width = parent.clientWidth;
      canvas.height = parent.clientHeight;
    };
    setSize();

    type Particle = {
      x: number;
      y: number;
      speed: number;
      opacity: number;
      fadeDelay: number;
      fadeStart: number;
      fadingOut: boolean;
    };

    let particles: Particle[] = [];
    let raf = 0;

    const count = () => Math.floor((canvas.width * canvas.height) / 10000);

    const make = (): Particle => {
      const fadeDelay = Math.random() * 600 + 100;
      return {
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        speed: Math.random() / 5 + 0.1,
        opacity: 0.5,
        fadeDelay,
        fadeStart: Date.now() + fadeDelay,
        fadingOut: false,
      };
    };

    const reset = (p: Particle) => {
      p.x = Math.random() * canvas.width;
      p.y = Math.random() * canvas.height;
      p.speed = Math.random() / 5 + 0.1;
      p.opacity = 0.5;
      p.fadeDelay = Math.random() * 600 + 100;
      p.fadeStart = Date.now() + p.fadeDelay;
      p.fadingOut = false;
    };

    const init = () => {
      particles = [];
      for (let i = 0; i < count(); i++) particles.push(make());
    };

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      particles.forEach((p) => {
        p.y -= p.speed;
        if (p.y < 0) reset(p);
        if (!p.fadingOut && Date.now() > p.fadeStart) p.fadingOut = true;
        if (p.fadingOut) {
          p.opacity -= 0.008;
          if (p.opacity <= 0) reset(p);
        }
        ctx.fillStyle = `rgba(49, 108, 236, ${p.opacity * 0.4})`;
        ctx.fillRect(p.x, p.y, 0.8, Math.random() * 2 + 1);
      });
      raf = requestAnimationFrame(draw);
    };

    const onResize = () => {
      setSize();
      init();
    };

    window.addEventListener("resize", onResize);
    init();
    raf = requestAnimationFrame(draw);

    return () => {
      window.removeEventListener("resize", onResize);
      cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-primary-50/60 via-background to-background py-24 sm:py-36 lg:py-44">
      {/* Particle canvas */}
      <canvas
        ref={canvasRef}
        className="pointer-events-none absolute inset-0 h-full w-full opacity-60"
        style={{ mixBlendMode: "multiply" }}
      />

      {/* Animated grid lines */}
      <div className="pointer-events-none absolute inset-0">
        <div className="hero-hline" style={{ top: "25%" }} />
        <div className="hero-hline" style={{ top: "50%" }} />
        <div className="hero-hline" style={{ top: "75%" }} />
        <div className="hero-vline" style={{ left: "25%" }} />
        <div className="hero-vline" style={{ left: "50%" }} />
        <div className="hero-vline" style={{ left: "75%" }} />
      </div>

      {/* Content */}
      <div className="container relative z-10">
        <div className="mx-auto max-w-3xl text-center">
          {kicker && (
            <p className="mb-4 text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground animate-fadeIn">
              {kicker}
            </p>
          )}
          <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-6xl lg:text-7xl animate-fadeIn">
            {title}
          </h1>
          <p className="mt-6 text-lg leading-8 text-muted-foreground sm:text-xl animate-slideUp">
            {subtitle}
          </p>
          <div className="mt-10 flex items-center justify-center gap-x-4 animate-slideUp">
            <Link
              href={primaryCta.href}
              className="rounded-lg bg-primary-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-primary-600/25 hover:bg-primary-500 transition-all hover:shadow-primary-600/40"
            >
              {primaryCta.label}
            </Link>
            <Link
              href={secondaryCta.href}
              className="group flex items-center gap-1 text-sm font-semibold text-foreground hover:text-primary-600 transition-colors"
            >
              {secondaryCta.label}
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
          </div>
        </div>
      </div>

      <style>{`
        .hero-hline, .hero-vline {
          position: absolute;
          opacity: 0;
        }
        .hero-hline {
          height: 1px;
          left: 0;
          right: 0;
          background: hsl(var(--border));
          transform: scaleX(0);
          transform-origin: 50% 50%;
          animation: hero-drawX 800ms cubic-bezier(.22,.61,.36,1) forwards;
        }
        .hero-hline:nth-child(1) { animation-delay: 150ms; }
        .hero-hline:nth-child(2) { animation-delay: 280ms; }
        .hero-hline:nth-child(3) { animation-delay: 410ms; }
        .hero-vline {
          width: 1px;
          top: 0;
          bottom: 0;
          background: hsl(var(--border));
          transform: scaleY(0);
          transform-origin: 50% 0%;
          animation: hero-drawY 900ms cubic-bezier(.22,.61,.36,1) forwards;
        }
        .hero-vline:nth-child(4) { animation-delay: 520ms; }
        .hero-vline:nth-child(5) { animation-delay: 640ms; }
        .hero-vline:nth-child(6) { animation-delay: 760ms; }
        @keyframes hero-drawX {
          0% { transform: scaleX(0); opacity: 0; }
          60% { opacity: 0.5; }
          100% { transform: scaleX(1); opacity: 0.3; }
        }
        @keyframes hero-drawY {
          0% { transform: scaleY(0); opacity: 0; }
          60% { opacity: 0.5; }
          100% { transform: scaleY(1); opacity: 0.3; }
        }
      `}</style>
    </section>
  );
}
