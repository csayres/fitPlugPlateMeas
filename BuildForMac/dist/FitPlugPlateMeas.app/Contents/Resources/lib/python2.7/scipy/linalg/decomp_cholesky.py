"""Cholesky decomposition functions."""

from numpy import asarray_chkfinite

# Local imports
from misc import LinAlgError, _datacopied
from lapack import get_lapack_funcs

__all__ = ['cholesky', 'cho_factor', 'cho_solve', 'cholesky_banded',
            'cho_solve_banded']


def _cholesky(a, lower=False, overwrite_a=False, clean=True):
    """Common code for cholesky() and cho_factor()."""

    a1 = asarray_chkfinite(a)
    if len(a1.shape) != 2 or a1.shape[0] != a1.shape[1]:
        raise ValueError('expected square matrix')

    overwrite_a = overwrite_a or _datacopied(a1, a)
    potrf, = get_lapack_funcs(('potrf',), (a1,))
    c, info = potrf(a1, lower=lower, overwrite_a=overwrite_a, clean=clean)
    if info > 0:
        raise LinAlgError("%d-th leading minor not positive definite" % info)
    if info < 0:
        raise ValueError('illegal value in %d-th argument of internal potrf'
                                                                    % -info)
    return c, lower

def cholesky(a, lower=False, overwrite_a=False):
    """Compute the Cholesky decomposition of a matrix.

    Returns the Cholesky decomposition, :math:`A = L L^*` or
    :math:`A = U^* U` of a Hermitian positive-definite matrix A.

    Parameters
    ----------
    a : ndarray, shape (M, M)
        Matrix to be decomposed
    lower : bool
        Whether to compute the upper or lower triangular Cholesky
        factorization.  Default is upper-triangular.
    overwrite_a : bool
        Whether to overwrite data in `a` (may improve performance).

    Returns
    -------
    c : ndarray, shape (M, M)
        Upper- or lower-triangular Cholesky factor of `a`.

    Raises
    ------
    LinAlgError : if decomposition fails.

    Examples
    --------
    >>> from scipy import array, linalg, dot
    >>> a = array([[1,-2j],[2j,5]])
    >>> L = linalg.cholesky(a, lower=True)
    >>> L
    array([[ 1.+0.j,  0.+0.j],
           [ 0.+2.j,  1.+0.j]])
    >>> dot(L, L.T.conj())
    array([[ 1.+0.j,  0.-2.j],
           [ 0.+2.j,  5.+0.j]])

    """
    c, lower = _cholesky(a, lower=lower, overwrite_a=overwrite_a, clean=True)
    return c


def cho_factor(a, lower=False, overwrite_a=False):
    """Compute the Cholesky decomposition of a matrix, to use in cho_solve

    Returns a matrix containing the Cholesky decomposition,
    ``A = L L*`` or ``A = U* U`` of a Hermitian positive-definite matrix `a`.
    The return value can be directly used as the first parameter to cho_solve.

    .. warning::
        The returned matrix also contains random data in the entries not
        used by the Cholesky decomposition. If you need to zero these
        entries, use the function `cholesky` instead.

    Parameters
    ----------
    a : array, shape (M, M)
        Matrix to be decomposed
    lower : boolean
        Whether to compute the upper or lower triangular Cholesky factorization
        (Default: upper-triangular)
    overwrite_a : boolean
        Whether to overwrite data in a (may improve performance)

    Returns
    -------
    c : array, shape (M, M)
        Matrix whose upper or lower triangle contains the Cholesky factor
        of `a`. Other parts of the matrix contain random data.
    lower : boolean
        Flag indicating whether the factor is in the lower or upper triangle

    Raises
    ------
    LinAlgError
        Raised if decomposition fails.

    See also
    --------
    cho_solve : Solve a linear set equations using the Cholesky factorization
                of a matrix.

    """
    c, lower = _cholesky(a, lower=lower, overwrite_a=overwrite_a, clean=False)
    return c, lower


def cho_solve((c, lower), b, overwrite_b=False):
    """Solve the linear equations A x = b, given the Cholesky factorization of A.

    Parameters
    ----------
    (c, lower) : tuple, (array, bool)
        Cholesky factorization of a, as given by cho_factor
    b : array
        Right-hand side

    Returns
    -------
    x : array
        The solution to the system A x = b

    See also
    --------
    cho_factor : Cholesky factorization of a matrix

    """

    b1 = asarray_chkfinite(b)
    c = asarray_chkfinite(c)
    if c.ndim != 2 or c.shape[0] != c.shape[1]:
        raise ValueError("The factored matrix c is not square.")
    if c.shape[1] != b1.shape[0]:
        raise ValueError("incompatible dimensions.")

    overwrite_b = overwrite_b or _datacopied(b1, b)

    potrs, = get_lapack_funcs(('potrs',), (c, b1))
    x, info = potrs(c, b1, lower=lower, overwrite_b=overwrite_b)
    if info != 0:
        raise ValueError('illegal value in %d-th argument of internal potrs'
                                                                    % -info)
    return x

def cholesky_banded(ab, overwrite_ab=False, lower=False):
    """Cholesky decompose a banded Hermitian positive-definite matrix

    The matrix a is stored in ab either in lower diagonal or upper
    diagonal ordered form:

        ab[u + i - j, j] == a[i,j]        (if upper form; i <= j)
        ab[    i - j, j] == a[i,j]        (if lower form; i >= j)

    Example of ab (shape of a is (6,6), u=2)::

        upper form:
        *   *   a02 a13 a24 a35
        *   a01 a12 a23 a34 a45
        a00 a11 a22 a33 a44 a55

        lower form:
        a00 a11 a22 a33 a44 a55
        a10 a21 a32 a43 a54 *
        a20 a31 a42 a53 *   *

    Parameters
    ----------
    ab : array, shape (u + 1, M)
        Banded matrix
    overwrite_ab : boolean
        Discard data in ab (may enhance performance)
    lower : boolean
        Is the matrix in the lower form. (Default is upper form)

    Returns
    -------
    c : array, shape (u+1, M)
        Cholesky factorization of a, in the same banded format as ab

    """
    ab = asarray_chkfinite(ab)

    pbtrf, = get_lapack_funcs(('pbtrf',), (ab,))
    c, info = pbtrf(ab, lower=lower, overwrite_ab=overwrite_ab)
    if info > 0:
        raise LinAlgError("%d-th leading minor not positive definite" % info)
    if info < 0:
        raise ValueError('illegal value in %d-th argument of internal pbtrf'
                                                                    % -info)
    return c


def cho_solve_banded((cb, lower), b, overwrite_b=False):
    """Solve the linear equations A x = b, given the Cholesky factorization of A.

    Parameters
    ----------
    (cb, lower) : tuple, (array, bool)
        `cb` is the Cholesky factorization of A, as given by cholesky_banded.
        `lower` must be the same value that was given to cholesky_banded.
    b : array
        Right-hand side
    overwrite_b : bool
        If True, the function will overwrite the values in `b`.

    Returns
    -------
    x : array
        The solution to the system A x = b

    See also
    --------
    cholesky_banded : Cholesky factorization of a banded matrix

    Notes
    -----

    .. versionadded:: 0.8.0

    """

    cb = asarray_chkfinite(cb)
    b = asarray_chkfinite(b)

    # Validate shapes.
    if cb.shape[-1] != b.shape[0]:
        raise ValueError("shapes of cb and b are not compatible.")

    pbtrs, = get_lapack_funcs(('pbtrs',), (cb, b))
    x, info = pbtrs(cb, b, lower=lower, overwrite_b=overwrite_b)
    if info > 0:
        raise LinAlgError("%d-th leading minor not positive definite" % info)
    if info < 0:
        raise ValueError('illegal value in %d-th argument of internal pbtrs'
                                                                    % -info)
    return x
