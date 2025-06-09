import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function isValidUrl(string: string): boolean {
  try {
    const url = new URL(string);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch (_) {
    return false;
  }
}

export function extractDomain(url: string): string {
  try {
    return new URL(url).hostname;
  } catch (_) {
    return url;
  }
}

export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(new Date(date));
}

export function formatDateTime(date: string | Date): string {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(date));
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

export function parseUrls(input: string): string[] {
  const lines = input.split('\n').map(line => line.trim()).filter(Boolean);
  const urls: string[] = [];
  
  for (const line of lines) {
    // Check if it's a comma-separated list
    if (line.includes(',')) {
      const commaSeparated = line.split(',').map(url => url.trim()).filter(Boolean);
      urls.push(...commaSeparated);
    } else {
      urls.push(line);
    }
  }
  
  return urls.filter(isValidUrl);
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'active':
      return 'text-green-600 bg-green-50';
    case 'captcha_blocked':
      return 'text-yellow-600 bg-yellow-50';
    case 'legal_blocked':
      return 'text-red-600 bg-red-50';
    case 'disabled':
      return 'text-gray-600 bg-gray-50';
    default:
      return 'text-gray-600 bg-gray-50';
  }
}

export function getStatusLabel(status: string): string {
  switch (status) {
    case 'active':
      return 'Active';
    case 'captcha_blocked':
      return 'CAPTCHA Blocked';
    case 'legal_blocked':
      return 'Legal Blocked';
    case 'disabled':
      return 'Disabled';
    default:
      return 'Unknown';
  }
} 