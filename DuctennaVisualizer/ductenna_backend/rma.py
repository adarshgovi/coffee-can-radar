import numpy as np
import scipy.interpolate

C = 3e8  # Speed of light in m/s
PI = np.pi

def feet2meters(feet):
    """Convert feet to meters."""
    return feet * 0.3048
def meters2feet(meters):
    """Convert meters to feet."""
    return meters / 0.3048

class RMA:
    """
    Implements the Range Migration Algorithm (RMA) for Synthetic Aperture Radar (SAR) image formation.

    Key processing steps include:
    - Hanning window smoothing to reduce spectral leakage
    - FFT across the synthetic aperture (cross-range) to obtain spatial frequency domain
    - Matched filtering to correct for parabolic wavefront curvature centered at distance Rs
    - Stolt interpolation to linearize range curvature across all scatterers
    - Inverse 2D FFT to reconstruct the SAR image in spatial coordinates

    Parameters:
        delta_x (float): Spacing between radar positions in meters (default: 2 inches = 0.0508 m)
        freq_range (tuple): Tuple (f_start, f_stop) representing chirp frequency range in Hz
        pulse_period (float): Duration of each chirp in seconds
        Rs (float): Distance to the center of the scene in meters

    Returns (from process()):
        dict: Contains 'sar_image', 'sif_padded', 'Kr', 'Kx', 'S_mf', 'S_st'"
    """

    def __init__(self, delta_x=None, freq_range=(2260e6, 2590e6), pulse_period=20e-3, Rs=9.0):
        self.freq_range = freq_range
        self.pulse_period = pulse_period
        self.Rs = Rs
        self.delta_x = delta_x or feet2meters(2/12.0)

    def process(self, sif):
        N, M = sif.shape
        bandwidth = self.freq_range[1] - self.freq_range[0]
        center_freq = self.freq_range[0] + bandwidth / 2
        Kr = np.linspace((4 * PI/C) * (center_freq - bandwidth/2), (4 * PI/C) * (center_freq + bandwidth/2), M)

        # Hanning window
        sif = sif * np.hanning(M)

        # Padding and Cross-range FFT (bascially converting S(x_n, w(t)) to S(K_x, K_r), where Kr is the range frequency and Kx is the cross frequency)
        padding = int(max(2048, N) - N) // 2
        padded_sif = np.pad(sif, [[padding, padding], [0, 0]], mode='constant')
        N = padded_sif.shape[0]
        Kx = np.linspace(-PI/self.delta_x, PI/self.delta_x, N)
        S = np.fft.fftshift(np.fft.fft(padded_sif, axis=0), axes=0)

        # Matched filtering
        # phi_mf(K_x, K_r) = Rs * sqrt(K_r^2 + K_x^2)
        Krr, Kxx = np.meshgrid(Kr, Kx)
        mf_phi = self.Rs * np.sqrt(Krr**2 + Kxx**2)
        mf_S = S * np.exp(1j * mf_phi)

        # Stolt interpolation
        kstart, kstop = 73, 108.5
        Ky_even = np.linspace(kstart, kstop, 1024)
        Ky = np.sqrt(Kr**2 - Kx**2)
        st_S = np.zeros((len(Kx), len(Ky_even)), dtype=np.complex128)
        for i in range(len(Kx)):
            interpolation_func = scipy.interpolate.interp1d(Ky[i], mf_S[i], bounds_error=False, fill_value=0)
            st_S[i] = interpolation_func(Ky_even)
        
        # Hanning window
        st_S = st_S * np.hanning(len(Ky_even))

        # Form 2D image from 2D IFFT
        image = np.fft.ifft2(st_S, s=(st_S.shape[0], st_S.shape[1]))
        image = np.fliplr(np.rot90(image))

        return {
            "image": image,
            "padded_sif": padded_sif,
            "Kx": Kx,
            "Kr": Kr,
            "mf_S": mf_S,
            "st_S": st_S,
        }
