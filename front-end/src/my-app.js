import { customElement } from 'aurelia';
import './my-app.css';
import myAppHtml from './my-app.html';

const TOKEN_KEY = 'booma_token';

function formatErrorDetail(detail) {
  if (detail == null) return '';
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => (typeof d === 'object' && d.msg ? d.msg : String(d))).join('; ');
  }
  return String(detail);
}

@customElement({
  name: 'my-app',
  template: myAppHtml,
})
export class MyApp {
  token = null;
  email = '';
  password = '';
  phoneStub = '';
  message = '';
  user = null;
  rides = [];
  savedAddresses = [];
  estimate = null;
  bookingBusy = false;
  view = 'login';
  loginTab = 'email';
  scheduleOpen = false;
  searchingOverlay = false;

  vehicleTiers = [
    { type: 'sedan', name: 'Economy', sub: 'Affordable · 4 seats', icon: '🚗' },
    { type: 'suv', name: 'Comfort', sub: 'Quieter ride · 4 seats', icon: '🚙' },
    { type: 'minivan', name: 'XL', sub: 'Spacious · 6 seats', icon: '🚐' },
  ];

  // Defaults align with references/data/synthetic-data.json: Sophie Zhang Home + Work,
  // same as ride_01HGKX3A1B2C3D4E5F6G7H8I pickup/destination.
  pickupLabel = '42 Glebe Point Road, Glebe NSW 2037';
  pickupLat = -33.8796;
  pickupLng = 151.1862;
  destLabel = '1 Macquarie Place, Sydney NSW 2000';
  destLat = -33.8617;
  destLng = 151.2099;
  vehicleType = 'sedan';

  get isLoggedOut() {
    return !this.token;
  }

  get isLoggedIn() {
    return !!this.token;
  }

  get hasNoRides() {
    return (this.rides?.length ?? 0) === 0;
  }

  get userInitials() {
    if (!this.user?.full_name) return '?';
    const p = this.user.full_name.trim().split(/\s+/).filter(Boolean);
    if (p.length >= 2) return (p[0][0] + p[p.length - 1][0]).toUpperCase();
    return p[0].slice(0, 2).toUpperCase();
  }

  get accountRoleLine() {
    if (!this.user) return '';
    const r = (this.user.role || 'passenger').replace(/^\w/, (c) => c.toUpperCase());
    return `${r} · prototype account`;
  }

  get mapOverlayTitle() {
    const line = (this.pickupLabel || '').split(',')[0].trim();
    return line || 'Pickup';
  }

  get mapOverlaySub() {
    if (!this.estimate) return 'Refresh estimate for trip time and distance';
    return `${this.estimate.duration_min} min · ${this.estimate.distance_km} km (stubbed route)`;
  }

  get estimateDistanceKm() {
    return this.estimate?.distance_km != null ? this.estimate.distance_km : '—';
  }

  get selectedVehicleOption() {
    return this.estimate?.vehicles?.find((v) => v.vehicle_type === this.vehicleType);
  }

  get fareBreakdown() {
    const opt = this.selectedVehicleOption;
    if (!opt) return null;
    const total = Number(opt.fare_estimate_aud);
    if (Number.isNaN(total)) return null;
    const base = Math.min(3, Math.max(2.2, total * 0.18));
    const booking = Math.max(1.2, total * 0.14);
    const dist = Math.max(0, total - base - booking);
    return {
      base: base.toFixed(2),
      dist: dist.toFixed(2),
      booking: booking.toFixed(2),
      total: total.toFixed(2),
    };
  }

  chipEmoji(label) {
    if (label === 'Home') return '🏠';
    if (label === 'Work') return '💼';
    return '📍';
  }

  tierFareDisplay(type) {
    const v = this.estimate?.vehicles?.find((x) => x.vehicle_type === type);
    if (!v) return '—';
    return `AUD ${Number(v.fare_estimate_aud).toFixed(2)}`;
  }

  tierEtaDisplay(type) {
    const v = this.estimate?.vehicles?.find((x) => x.vehicle_type === type);
    if (!v) return '—';
    return `${v.eta_min} min away`;
  }

  rideIcon(vehicleType) {
    const m = { sedan: '🚗', suv: '🚙', minivan: '🚐' };
    return m[vehicleType] || '🚗';
  }

  vehicleTierName(vehicleType) {
    const t = this.vehicleTiers.find((x) => x.type === vehicleType);
    return t ? t.name : vehicleType;
  }

  rideRouteLine(ride) {
    const a = this.shortAddr(ride.pickup_address);
    const b = this.shortAddr(ride.destination_address);
    return `${a} → ${b}`;
  }

  shortAddr(s) {
    if (!s) return '';
    return s.length > 40 ? `${s.slice(0, 38)}…` : s;
  }

  formatRideWhen(iso) {
    if (!iso) return '—';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return String(iso);
    const now = new Date();
    const sameDay = d.toDateString() === now.toDateString();
    if (sameDay) {
      return new Intl.DateTimeFormat('en-AU', { hour: 'numeric', minute: '2-digit' }).format(d);
    }
    const opts = {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
      hour: 'numeric',
      minute: '2-digit',
    };
    if (d.getFullYear() !== now.getFullYear()) {
      opts.year = 'numeric';
    }
    return new Intl.DateTimeFormat('en-AU', opts).format(d);
  }

  displayRideFare(ride) {
    const n = ride.fare_final ?? ride.fare_estimate;
    if (n == null) return '—';
    return `AUD ${Number(n).toFixed(2)}`;
  }

  statusPillClass(status) {
    const s = (status || '').toUpperCase();
    if (s === 'COMPLETED') return 'status-completed';
    if (s === 'CANCELLED') return 'status-cancelled';
    return 'status-live';
  }

  setLoginTab(tab) {
    this.loginTab = tab;
    this.message = '';
  }

  switchNav(screen) {
    this.view = screen;
  }

  toggleSchedule() {
    this.scheduleOpen = !this.scheduleOpen;
  }

  forgotStub() {
    this.message = 'Prototype: password reset is not implemented. All seeded users use the demo password.';
  }

  phoneOtpStub() {
    this.message = 'Prototype: SMS OTP is not wired. Use the Email tab with a seeded account.';
  }

  oauthStub(kind) {
    this.message = `Prototype: ${kind} sign-in is not wired. Use email + demo password.`;
  }

  cancelSearch() {
    this.searchingOverlay = false;
    this.bookingBusy = false;
  }

  async attached() {
    const stored = sessionStorage.getItem(TOKEN_KEY);
    if (stored) {
      this.token = stored;
      await this.bootstrapAuthed();
    }
  }

  authHeaders() {
    return {
      Authorization: `Bearer ${this.token}`,
      'Content-Type': 'application/json',
    };
  }

  async bootstrapAuthed() {
    this.message = '';
    try {
      await this.loadMe();
      await this.loadRides();
      await this.loadSaved();
      this.view = 'book';
      await this.getEstimate();
    } catch (e) {
      this.message = e.message || 'Session expired; please sign in again.';
      this.logout();
    }
  }

  async loadMe() {
    const r = await fetch('/api/v1/users/me', { headers: this.authHeaders() });
    if (!r.ok) throw new Error('Could not load profile');
    this.user = await r.json();
  }

  async loadRides() {
    const r = await fetch('/api/v1/bookings', { headers: this.authHeaders() });
    if (!r.ok) throw new Error('Could not load rides');
    this.rides = await r.json();
  }

  async loadSaved() {
    const res = await fetch('/api/v1/users/saved-addresses', { headers: this.authHeaders() });
    if (!res.ok) {
      this.savedAddresses = [];
      return;
    }
    this.savedAddresses = await res.json();
  }

  async login() {
    this.message = '';
    let r;
    try {
      r = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: this.email, password: this.password }),
      });
    } catch {
      this.message =
        'Cannot reach API. Start the backend (uvicorn on port 8000) and use the dev server (npm start on port 9000) so /api is proxied.';
      return;
    }
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      this.message = formatErrorDetail(err.detail) || 'Login failed';
      return;
    }
    const data = await r.json();
    this.token = data.access_token;
    sessionStorage.setItem(TOKEN_KEY, this.token);
    await this.bootstrapAuthed();
  }

  logout() {
    sessionStorage.removeItem(TOKEN_KEY);
    this.token = null;
    this.user = null;
    this.rides = [];
    this.savedAddresses = [];
    this.estimate = null;
    this.message = '';
    this.view = 'login';
    this.searchingOverlay = false;
  }

  applySaved(addr) {
    this.pickupLabel = addr.formatted_address;
    this.pickupLat = addr.lat;
    this.pickupLng = addr.lng;
    this.getEstimate().catch(() => {});
  }

  applySavedDest(addr) {
    this.destLabel = addr.formatted_address;
    this.destLat = addr.lat;
    this.destLng = addr.lng;
    this.getEstimate().catch(() => {});
  }

  selectVehicleType(tier) {
    this.vehicleType = tier.type;
    this.getEstimate().catch(() => {});
  }

  async getEstimate() {
    if (!this.token) return;
    this.message = '';
    const q = new URLSearchParams({
      pickup_lat: String(this.pickupLat),
      pickup_lng: String(this.pickupLng),
      destination_lat: String(this.destLat),
      destination_lng: String(this.destLng),
      vehicle_type: this.vehicleType,
    });
    const r = await fetch(`/api/v1/bookings/estimate?${q}`, { headers: this.authHeaders() });
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      this.message = formatErrorDetail(err.detail) || 'Estimate failed';
      this.estimate = null;
      return;
    }
    this.estimate = await r.json();
  }

  async createBooking() {
    this.bookingBusy = true;
    this.message = '';
    this.searchingOverlay = true;
    try {
      const r = await fetch('/api/v1/bookings', {
        method: 'POST',
        headers: this.authHeaders(),
        body: JSON.stringify({
          pickup_address: this.pickupLabel,
          pickup_lat: this.pickupLat,
          pickup_lng: this.pickupLng,
          destination_address: this.destLabel,
          destination_lat: this.destLat,
          destination_lng: this.destLng,
          vehicle_type: this.vehicleType,
        }),
      });
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        this.message = formatErrorDetail(err.detail) || 'Booking failed';
        return;
      }
      await this.loadRides();
      await this.getEstimate();
      this.message = 'Ride requested. Driver matching is stubbed in the prototype.';
    } finally {
      this.searchingOverlay = false;
      this.bookingBusy = false;
    }
  }

  async tryAutocomplete() {
    this.message = '';
    const r = await fetch('/api/v1/stub/maps/autocomplete?q=sydney', { headers: this.authHeaders() });
    if (!r.ok) return;
    const list = await r.json();
    this.message = `Stub maps returned ${list.length} suggestion(s) (see console).`;
    console.info('stub maps autocomplete', list);
  }

  async tryStubPayment() {
    const r = await fetch('/api/v1/stub/payments/setup-intent', {
      method: 'POST',
      headers: this.authHeaders(),
    });
    if (!r.ok) return;
    const data = await r.json();
    this.message = `Stub payment intent: ${data.payment_intent_id}`;
  }
}
