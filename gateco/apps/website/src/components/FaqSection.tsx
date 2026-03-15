'use client';

import { useState } from 'react';
import { ChevronDown } from 'lucide-react';

function FaqItem({ question, answer }: { question: string; answer: string }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="py-4">
      <button
        type="button"
        className="flex w-full items-center justify-between text-left"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        <span className="text-base font-medium text-foreground">{question}</span>
        <ChevronDown className={`h-5 w-5 text-muted-foreground transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <p className="mt-3 text-muted-foreground">{answer}</p>
      )}
    </div>
  );
}

export default function FaqSection({ items }: { items: { question: string; answer: string }[] }) {
  return (
    <div className="mx-auto mt-12 max-w-3xl divide-y divide-border">
      {items.map((item, index) => (
        <FaqItem key={index} question={item.question} answer={item.answer} />
      ))}
    </div>
  );
}
