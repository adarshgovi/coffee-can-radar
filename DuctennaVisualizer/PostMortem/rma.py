import numpy as np
from scipy.interpolate import interp1d

C = 3e8  # Speed of light in m/s
PI = np.pi

def feet2meters(feet):
    """Convert feet to meters."""
    return feet * 0.3048
def meters2feet(meters):
    """Convert meters to feet."""
    return meters / 0.3048

class RMA:
    def __init__(self, Kr, Xa, delta_x, Rs, kstart=73, kstop=108.5, zpad=2048):
        self.Kr = Kr
        self.Xa = Xa
        self.delta_x = delta_x
        self.Rs = Rs
        self.kstart = kstart
        self.kstop = kstop
        self.zpad = zpad
        self.c = 3e8

    def dbv(self, x):
        return 20 * np.log10(np.abs(x))

    def apply_custom_hanning(self, N):
        return 0.5 + 0.5 * np.cos(2 * np.pi * (np.arange(N) - N / 2) / N)

    def process(self, sif):
        # Step 1: Apply Hanning window in fast time
        N = sif.shape[1]
        H = self.apply_custom_hanning(N)
        sif = sif * H

        # Step 2: Zero pad in cross-range
        padded = np.zeros((self.zpad, sif.shape[1]), dtype=complex)
        start = (self.zpad - sif.shape[0]) // 2
        padded[start:start + sif.shape[0], :] = sif
        sif = padded

        # Step 3: FFT along cross-range
        S = np.fft.fftshift(np.fft.fft(sif, axis=0), axes=0)
        Kx = np.linspace(-np.pi / self.delta_x, np.pi / self.delta_x, S.shape[0])

        # Step 4: Matched filtering
        Krr, Kxx = np.meshgrid(self.Kr, Kx)
        phi_mf = self.Rs * np.sqrt(Krr**2 - Kxx**2)
        S_mf = S * np.exp(1j * phi_mf)

        # Step 5: Stolt interpolation
        Ky_even = np.linspace(self.kstart, self.kstop, 1024)
        S_st = np.zeros((S_mf.shape[0], len(Ky_even)), dtype=np.complex128)
        for i in range(S_mf.shape[0]):
            Ky = np.sqrt(self.Kr**2 - Kx[i]**2)
            interp_func = interp1d(Ky, S_mf[i], bounds_error=False, fill_value=0)
            S_st[i] = interp_func(Ky_even)

        S_st[np.isnan(S_st)] = 1e-30

        # Step 6: Apply Hanning in range dimension
        H = self.apply_custom_hanning(S_st.shape[1])
        S_st = S_st * H

        # Step 7: 2D IFFT with 4x zero padding
        image = np.fft.ifft2(S_st, s=(S_st.shape[0]*4, S_st.shape[1]*4))
        image = np.fliplr(np.rot90(image))

        # Step 8: Final cropping and scaling
        bw = self.c * (self.kstop - self.kstart) / (4 * np.pi)
        max_range = (self.c * S_st.shape[1]) / (2 * bw) / 0.3048  # in ft

        cr1, cr2 = -80, 80  # ft
        dr1, dr2 = 1 + self.Rs / 0.3048, 350 + self.Rs / 0.3048  # ft

        dr_index1 = round((dr1 / max_range) * image.shape[0])
        dr_index2 = round((dr2 / max_range) * image.shape[0])
        cr_index1 = round(((cr1 + self.zpad * self.delta_x / (2 * 0.3048)) / (self.zpad * self.delta_x / 0.3048)) * image.shape[1])
        cr_index2 = round(((cr2 + self.zpad * self.delta_x / (2 * 0.3048)) / (self.zpad * self.delta_x / 0.3048)) * image.shape[1])

        trunc_image = image[dr_index1:dr_index2, cr_index1:cr_index2]

        downrange = np.linspace(-dr1, -dr2, trunc_image.shape[0]) + self.Rs / 0.3048
        crossrange = np.linspace(cr1, cr2, trunc_image.shape[1])

        for i in range(trunc_image.shape[1]):
            trunc_image[:, i] *= np.abs(downrange * 0.3048)**(3/2)

        trunc_image_dB = self.dbv(trunc_image)

        return trunc_image_dB, crossrange, downrange
