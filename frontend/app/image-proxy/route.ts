import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const url = searchParams.get('url');

    if (!url) {
      return new NextResponse('Missing url parameter', { status: 400 });
    }
    if (!/^https?:\/\//i.test(url)) {
      return new NextResponse('Invalid url', { status: 400 });
    }

    const upstream = await fetch(url, {
      method: 'GET',
      headers: {
        'User-Agent': 'GenealogyTree/1.0 (+http://localhost:3000)',
        'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
        'Referer': 'https://commons.wikimedia.org/',
      },
      redirect: 'follow',
      cache: 'no-store',
    });

    if (!upstream.ok) {
      return new NextResponse(`Upstream error: ${upstream.status}`, { status: 502 });
    }

    const contentType = upstream.headers.get('content-type') || 'image/jpeg';
    const arrayBuf = await upstream.arrayBuffer();

    return new NextResponse(Buffer.from(arrayBuf), {
      status: 200,
      headers: {
        'Content-Type': contentType,
        'Cache-Control': 'public, max-age=86400',
        'Access-Control-Allow-Origin': '*',
      },
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'unknown';
    return new NextResponse(`Proxy error: ${message}`, { status: 500 });
  }
}
