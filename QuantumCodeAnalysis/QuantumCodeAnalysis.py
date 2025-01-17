"""Functions to analyse quantum codes
"""
from itertools import combinations
import numpy as np
# from sage.all import GF, matrix, vector, Permuations, copy, LinearCode
import flinalg as fl


def low_weight_logical(gen1, gen2, trials):
    """
    Monte Carlo algorithm which tries to find the lowest weight code word of G1
    which has odd overlap with code words in G2.
    INPUT: Two linear codes given by generating matrices of shape kxn. Number of Monte Carlo trials.
    OUTPUT: A code word of G1 with low weight.
    """
    uig1 = np.array(gen1, dtype='uint8')
    uig2 = np.array(gen2, dtype='uint8')
    _, col1 = gen1.shape
    min_d = col1
    min_logical = None
    total_permutation = np.arange(col1)
    for _ in range(trials):
        perm = np.random.permutation(col1)
        uig1 = uig1[:, perm]
        _, permstdf = fl.standard_form(uig1)
        uig2 = uig2[:, perm][:, permstdf]
        total_permutation = total_permutation[perm][permstdf]
        updated = False
        for vec in uig1:
            ham_vec = sum(vec % 2)
            if ham_vec < min_d and (sum(np.dot(uig2, vec) % 2) > 0):
                min_d = ham_vec
                min_logical = vec
                updated = True
        if not updated:
            min_logical = min_logical[perm][permstdf]
    return min_logical, total_permutation


def distance_upper_bound(logicalx, checkx, logicalz, checkz, trials):
    """
    Monte Carlo algorithm which upper bounds the distance of a CSS quantum code
    INPUT: Two linear codes given by generating matrices of shape kxn. Number of Monte Carlo trials.
    OUTPUT: Upper bound on code distance.
    """
    lowx, _ = low_weight_logical(np.block([[logicalx], [checkx]]), logicalz, trials)
    lowz, _ = low_weight_logical(np.block([[logicalz], [checkz]]), logicalx, trials)
    disx = lowx.hamming_weight()
    disz = lowz.hamming_weight()
    return min(disx, disz)


def distance_lower_bound(checks, logicals, lower_dist):
    """Checks all weight lower_dist vector for if they
    are logical operators, i.e. commutes with checks but
    not with logicals.
    """
    _, n = checks.shape
    candidate_logical = np.zeros((n,), dtype='uint8')
    for indices in combinations(range(n), lower_dist):
        for j in indices:
            candidate_logical[j] = 1
        if ((np.dot(checks, candidate_logical) % 2).sum() == 0) and (np.dot(logicals, candidate_logical) % 2).any():
            return (False, candidate_logical)
        for j in indices:
            candidate_logical[j] = 0
    return (True, None)


def list_low_log(checks, logicals, lower_dist):
    """Returns all weight lower_dist vector if they
    are logical operators, i.e. commutes with checks but
    not with logicals.
    """
    _, n = checks.shape
    list_log = []
    candidate_logical = np.zeros((n,), dtype='uint8')
    for indices in combinations(range(n), lower_dist):
        for j in indices:
            candidate_logical[j] = 1
        if ((np.dot(checks, candidate_logical) % 2).sum() == 0) and (np.dot(logicals, candidate_logical) % 2).any():
            list_log.append(np.copy(candidate_logical))
        for j in indices:
            candidate_logical[j] = 0
    return list_log


def logicals(hmatx, hmatz):
    """Finds and returns logical operators
    from the import X and Z checks in hmatx and hmatz
    """
    uintmatx = np.array(hmatx, dtype='uint8')
    uintmatz = np.array(hmatz, dtype='uint8')
    kerx = fl.kernel(np.transpose(uintmatx))
    kerz = fl.kernel(np.transpose(uintmatz))
    logicalxspace, _ = fl.quotient_basis(kerz, uintmatx)
    logicalzspace, _ = fl.quotient_basis(kerx, uintmatz)
    return (logicalxspace, logicalzspace)


def logical_circuit(logicalx, k_orth):
    """find the kth level equivalent logical circuit
    for a transversal application of R(k_orth) on
    the code given all the logical X operators
    """
    k = len(logicalx)
    logicalx_index = list(zip(range(k), logicalx))
    gates = [[] for _ in range(k_orth)]
    for j, jgates in enumerate(gates):
        for tupl in combinations(logicalx_index, j + 1):
            indices, logs = zip(*tupl)
            wedge = [int(np.prod(t)) for t in zip(*logs)]
            coef = ((-1)**j * 2**j * sum(wedge)) \
                % (2**k_orth)
            if coef != 0:
                jgates.append((indices, coef))
    return gates


def get_partner(l, G):
    """find indices of rows of G which have odd overlap with l"""
    p = np.dot(G, l)
    p = np.mod(p, 2)
    return p.nonzero()[0]


def gram_schmidt(u, v, A):
    """Removes v from the row-span of A"""
    w = np.dot(A, u)
    w = np.mod(w, 2)
    B = A + np.outer(w, v)
    B = np.mod(B, 2)
    return B
