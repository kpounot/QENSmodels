from __future__ import print_function
import numpy as np

try:
    import QENSmodels
except ImportError:
    print('Module QENSmodels not found')


def hwhmJumpSitesLogNormDist(q, N=3, radius=1.0, resTime=1.0, sigma=1.0):
    """ Returns some characteristics of `JumpSitesLogNormDist`

    Parameters
    ----------

    q: float, list or :class:`~numpy:numpy.ndarray`
        momentum transfer (in 1/Angstrom)

    N: integer
        number of sites in circle. Default to 3.

    radius: float
        radius of the circle (in Angstrom). Default to 1.

    resTime: float
        residence time (in NEED TO CHECK UNITS). Default to 1.

    sigma: float
        standard deviation of the Gaussian distribution. Default to 1.

    Returns
    -------

    hwhm: :class:`~numpy:numpy.ndarray`
        half-width half maximum

    eisf: :class:`~numpy:numpy.ndarray`
        elastic incoherent structure factor

    qisf: :class:`~numpy:numpy.ndarray`
        quasi-elastic incoherent structure factor


    Examples
    --------
    >>> hwhm, eisf, qisf = hwhmJumpSitesLogNormDist([1., 2.], 0.5, 1.5, 1.0)
    >>> round(hwhm[0], 3), round(hwhm[1], 3)
    (0.286, 0.5)
    >>> eisf
    array([0., 0.])
    >>> qisf
    array([1., 1.])

    Notes
    -----

    """
    # Input validation
    if radius <= 0:
        raise ValueError("radius, the radius of the circle, "
                         "should be positive")
    if resTime < 0:
        raise ValueError("resTime, the residence time, "
                         "should be positive")
    if N < 2:
        raise ValueError("the minimum number of sites N is 2")

    q = np.asarray(q, dtype=np.float32)

    # number of sites has to be an integer
    N = np.int(N)

    hwhm_equiv, eisf, qisf_equiv = \
        QENSmodels.hwhmEquivalentSitesCircle(q, N, radius, resTime)

    # number of lorentzians used in distribution is 2 * nmax + 1
    n_max = 10

    # lower value of gi / max(gi) to be used
    low_lim = 0.1

    # max(absolute) value of log(x) range to explore
    range_gamma = sigma * np.sqrt(-2.0 * np.log(low_lim))

    dgamma = range_gamma / float(n_max)
    # vector of gamma_i / gamma_average values to use
    ratio = np.exp(np.arange(2 * n_max + 1) * dgamma - range_gamma)

    # distribution  of weights

    gi = np.exp(-0.5 * np.log(ratio) ** 2 / sigma ** 2)
    gi /= np.sum(gi)  # normalize so sum gi = 1

    # distribution of hwhm for each jumping distance
    hwhm = np.zeros((q.size, N, 2 * n_max + 1))
    for qiter in range(q.size):
        for isite in range(N):
            # corresponding hwhm for each gi and jumping distance
            hwhm[qiter, isite, :] = hwhm_equiv[qiter, isite] * ratio

    # quasielastic terms
    qisf = np.zeros((q.size, N-1, 2 * n_max + 1))
    for qiter in range(q.size):
        for ilor in range(2 * n_max + 1):
            for isite in range(0, N-1):
                qisf[qiter, isite, ilor] = qisf_equiv[qiter, isite] * gi[ilor]

    return hwhm, eisf, qisf


def sqwJumpSitesLogNormDist(w, q, scale=1.0, center=0.0, N=3,
                            radius=1.0, resTime=1.0, sigma=1.):
    r""" Model of jumps between N equivalent sites in a circle with a log-norm
    distribution of relaxation times

    Parameters
    ----------

    w: list or :class:`~numpy:numpy.ndarray`
        energy transfer (in ps)

    q: float, list or :class:`~numpy:numpy.ndarray`
        momentum transfer (non-fitting, in 1/Angstrom)

    scale: float
        scale factor. Default to 1.

    center: float
        center of peak. Default to 0.

    N: integer
        number of sites in circle. Default to 3.

    radius: float
        radius of rotation (in Angstrom). Default to 1.

    resTime: float
        residence time in a site before jumping to another site (in 1/ps).
        Default to 1.

    sigma: float
        standard deviation of the Gaussian distribution. Default to 1.

    Return
    ------
    :class:`~numpy:numpy.ndarray`
        output array

    Examples
    --------

    >>> sqw = sqwJumpSitesLogNormDist([1, 2, 3], [0.3, 0.4], 1, 0, 5, 1, 1, 1)
    >>> round(sqw[0, 0], 4)
    0.0035
    >>> round(sqw[0, 1], 4)
    0.0014
    >>> round(sqw[0, 2], 4)
    0.0008
    >>> round(sqw[1, 0], 3)
    0.0061
    >>> round(sqw[1, 1], 4)
    0.0025
    >>> round(sqw[1, 2], 4)
    0.0014

    >>> sqw = sqwJumpSitesLogNormDist(1, 1, 1, 0, 4, 1, 1, 1)
    >>> round(sqw[0], 4)
    0.0344


    Notes
    -----

    * The `sqwJumpSitesLogNorm` is expressed as

      .. math::

          S(q, \omega) =


    Reference
    ----------

    A. Chahid, A. Alegria, and J. Colmenero,
    **Macromolecules** *27*, 3282-3288 (1994)
    `link <https://pubs.acs.org/doi/abs/10.1021/ma00090a022>`_


    """
    # Input validation

    w = np.asarray(w)

    q = np.asarray(q, dtype=np.float32)

    # Create output array
    sqw = np.zeros((q.size, w.size))

    # Get widths, EISFs and QISFs of model
    hwhm, eisf, qisf = hwhmJumpSitesLogNormDist(q, N, radius, resTime, sigma)
    # Number of Lorentzians (= N-1)
    numberLorentz = hwhm.shape[1] - 1
    # Number of samples for Gaussian distribution
    numberSamplingDistrib = hwhm.shape[2]
    # Sum of Lorentzians
    # (Note that hwhm has dimensions [q.size, N], as hwhm[:,0]
    # contains a width=0, corresponding to the elastic line
    # (eisf), while qisf has dimensions [q.size, N-1])
    for i in range(q.size):
        # elastic term
        sqw[i, :] = eisf[i] * QENSmodels.delta(w, scale, center)
        for j in range(numberLorentz):
            for k in range(numberSamplingDistrib):
                # quasielastic terms
                sqw[i, :] += qisf[i, j, k] * \
                             QENSmodels.lorentzian(w,
                                                   scale,
                                                   center,
                                                   hwhm[i, j + 1, k])

    # For Bumps use (needed for final plotting)
    # Using a 'Curve' in bumps for each Q --> needs vector array
    if q.size == 1:
        sqw = np.reshape(sqw, w.size)

    return sqw


if __name__ == "__main__":
    import doctest
    doctest.testmod()
