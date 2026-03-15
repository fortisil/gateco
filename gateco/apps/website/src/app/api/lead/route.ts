import { NextResponse } from 'next/server';

interface LeadPayload {
  name: string;
  email: string;
  message?: string;
}

export async function POST(request: Request) {
  try {
    const body: LeadPayload = await request.json();

    if (!body.name || !body.email) {
      return NextResponse.json(
        { error: 'Name and email are required' },
        { status: 400 }
      );
    }

    const webhookUrl = process.env.LEAD_WEBHOOK_URL;
    if (!webhookUrl) {
      console.error('LEAD_WEBHOOK_URL not configured');
      return NextResponse.json(
        { error: 'Lead capture not configured' },
        { status: 500 }
      );
    }

    const response = await fetch(webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: body.name,
        email: body.email,
        message: body.message || '',
        timestamp: new Date().toISOString(),
        source: 'website',
      }),
    });

    if (!response.ok) {
      console.error('Webhook error:', response.status);
      return NextResponse.json({ error: 'Failed to submit' }, { status: 500 });
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Lead capture error:', error);
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
