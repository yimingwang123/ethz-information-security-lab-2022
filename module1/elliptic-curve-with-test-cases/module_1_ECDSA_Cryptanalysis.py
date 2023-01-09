import math
import random
from fpylll import LLL
from fpylll import BKZ
from fpylll import IntegerMatrix
from fpylll import CVP
from fpylll import SVP
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


# Euclidean algorithm for gcd computation
def egcd(a, b):
    if a == 0:
        return b, 0, 1
    else:
        g, y, x = egcd(b % a, a)
        return g, x - (b // a) * y, y

# Modular inversion computation
def mod_inv(a, p):
    if a < 0:
        return p - mod_inv(-a, p)
    g, x, y = egcd(a, p)
    if g != 1:
        raise ArithmeticError("Modular inverse does not exist")
    else:
        return x % p

def check_x(x, Q):
    """ Given a guess for the secret key x and a public key Q = [x]P,
        checks if the guess is correct.

        :params x:  secret key, as an int
        :params Q:  public key, as a tuple of two ints (Q_x, Q_y)
    """
    x = int(x)
    if x <= 0:
        return False
    Q_x, Q_y = Q
    sk = ec.derive_private_key(x, ec.SECP256R1())
    pk = sk.public_key()
    xP = pk.public_numbers()
    return xP.x == Q_x and xP.y == Q_y

def recover_x_known_nonce(k, h, r, s, q):
    return (mod_inv(r, q) * (k * s - h)) % q

def recover_x_repeated_nonce(h_1, r_1, s_1, h_2, r_2, s_2, q):
    return ((h_1 * s_2 - h_2 * s_1) * mod_inv(r_2 * s_1 - r_1 * s_2, q)) % q

def bits_to_integer(list_of_bits):
    # return the integer represented by this list of bits
    accumulated = 0
    for bit in list_of_bits:
        accumulated *= 2
        accumulated += bit

    return accumulated

def MSB_to_Padded_Int(N, L, list_k_MSB):
    a = bits_to_integer(list_k_MSB)
    return a * 2 ** (N - L) + 2 ** (N - L - 1)

def LSB_to_Int(list_k_LSB):
    return bits_to_integer(list_k_LSB)

def setup_hnp_single_sample(N, L, list_k_MSB, h, r, s, q, givenbits="msbs", algorithm="ecdsa"):
    # A function that sets up a single instance for the hidden number problem (HNP)
    # The function is given a list of the L most significant bts of the N-bit nonce k, along with (h, r, s) and the base point order q
    # The function should return (t, u) computed as described in the lectures
    # In the case of EC-Schnorr, r may be set to h
    if givenbits == 'msbs':
        if algorithm == 'ecdsa':
            t = r * mod_inv(s, q) % q
            z = h * mod_inv(s, q) % q
            u = (MSB_to_Padded_Int(N, L, list_k_MSB) - z) % q
        else:
            t = r % q
            u = (MSB_to_Padded_Int(N, L, list_k_MSB) - s) % q
    else:
        if algorithm == 'ecdsa':
            factor_inverse = mod_inv(2 ** L, q)
            t = r * mod_inv(s, q) * factor_inverse % q
            u = (2 ** (N - 1 - L) + LSB_to_Int(list_k_MSB) * factor_inverse - h * mod_inv(s, q) * factor_inverse) % q
        else:
            factor_inverse = mod_inv(2 ** L, q)
            t = factor_inverse * r % q
            u = (factor_inverse * LSB_to_Int(list_k_MSB) + 2 ** (N - L - 1) - factor_inverse * s) % q
    return t, u

def setup_hnp_all_samples(N, L, num_Samples, listoflists_k_MSB, list_h, list_r, list_s, q, givenbits="msbs", algorithm="ecdsa"):
    # A function that sets up n = num_Samples many instances for the hidden number problem (HNP)
    # For each instance, the function is given a list the L most significant bits of the N-bit nonce k, along with (h, r, s) and the base point order q
    # The function should return a list of t values and a list of u values computed as described in the lectures
    list_t = []
    list_u = []
    for i in range(num_Samples):
        t, u = setup_hnp_single_sample(N, L, listoflists_k_MSB[i], list_h[i], list_r[i], list_s[i], q, givenbits,
                                       algorithm)
        list_t.append(t)
        list_u.append(u)

    return list_t, list_u

def hnp_to_cvp(N, L, num_Samples, list_t, list_u, q):
    # A function that takes as input an instance of HNP and converts it into an instance of the closest vector problem (CVP)
    # The function is given as input a list of t values, a list of u values and the base point order q
    # The function should return the CVP basis matrix B (to be implemented as a nested list) and the CVP target vector u (to be implemented as a list)
    # u is actually an integer, so we only need to scale the matrix
    scaling_factor = 2 ** (L + 1)
    B = []
    for row_index in range(num_Samples + 1):
        if row_index < num_Samples:
            # not the last row
            row = [0] * (num_Samples + 1)
            row[row_index] = q * scaling_factor
        else:
            # last row
            row = [list_t[col_index] * scaling_factor if col_index < num_Samples else 1
                   for col_index in range(num_Samples + 1)]

        B.append(row)

    u = [list_u[index] * scaling_factor for index in range(num_Samples)] + [0]
    return B, u
def get_magic_M(N, L, num_Samples, cvp_basis_B, cvp_list_u):
    norm = (num_Samples + 1) ** (1/2) * 2 ** (N - L - 1)
    return round(norm)

def cvp_to_svp(N, L, num_Samples, cvp_basis_B, cvp_list_u):
    # first do LLL on cvp_basis_B, in order to find its smallest vector length lambda_1
    M = get_magic_M(N, L, num_Samples, cvp_basis_B, cvp_list_u)
    svp_basis_B = []
    for row_index in range(num_Samples + 2):
        if row_index < num_Samples + 1:
            row = cvp_basis_B[row_index] + [0]
        else:
            row = cvp_list_u + [M]
        svp_basis_B.append(row)

    return svp_basis_B


def solve_cvp(cvp_basis_B, cvp_list_u):
    matrix_B = IntegerMatrix.from_matrix(cvp_basis_B)
    reduced_B = LLL.reduction(matrix_B, method=solving_method)
    return list(CVP.closest_vector(reduced_B, cvp_list_u, method=solving_method))

def solve_svp(svp_basis_B):
    candidate_sols = []
    max_candidate_rows = min(10, len(svp_basis_B))
    matrix_B = IntegerMatrix.from_matrix(svp_basis_B)
    reduced_B = LLL.reduction(matrix_B, method=solving_method)
    for row_index in range(max_candidate_rows):
        candidate_sols.append(list(reduced_B[row_index]))
    return candidate_sols


def recover_x_partial_nonce_CVP(Q, N, L, num_Samples, listoflists_k_MSB, list_h, list_r, list_s, q, givenbits="msbs", algorithm="ecdsa"):
    # "repeated nonces" cryptanalytic attack on ECDSA and EC-Schnorr using the in-built CVP-solver functions from the fpylll library
    list_t, list_u = setup_hnp_all_samples(N, L, num_Samples, listoflists_k_MSB, list_h, list_r, list_s, q)
    cvp_basis_B, cvp_list_u = hnp_to_cvp(N, L, num_Samples, list_t, list_u, q)
    v_List = solve_cvp(cvp_basis_B, cvp_list_u)
    last_element = v_List[-1]
    private_key = last_element % q
    return private_key

def recover_x_partial_nonce_SVP(Q, N, L, num_Samples, listoflists_k_MSB, list_h, list_r, list_s, q, givenbits="msbs", algorithm="ecdsa"):
    # "repeated nonces" cryptanalytic attack on ECDSA and EC-Schnorr using the in-built CVP-solver functions from the fpylll library
    list_t, list_u = setup_hnp_all_samples(N, L, num_Samples, listoflists_k_MSB, list_h, list_r, list_s, q)
    cvp_basis_B, cvp_list_u = hnp_to_cvp(N, L, num_Samples, list_t, list_u, q)
    svp_basis_B = cvp_to_svp(N, L, num_Samples, cvp_basis_B, cvp_list_u)
    list_of_f_List = solve_svp(svp_basis_B)
    for sol_id, sol in enumerate(list_of_f_List):
        last_element = sol[-1]
        if last_element == 0:
            continue
        sign = 1 if last_element > 0 else -1
        last_element_in_cvp_sol = cvp_list_u[-1] - sign * sol[-2]
        candidate_key = last_element_in_cvp_sol % q
        if check_x(candidate_key, Q):
            return candidate_key
    return 0



# testing code

from module_1_ECDSA_Cryptanalysis_tests import run_tests

run_tests(recover_x_known_nonce,
    recover_x_repeated_nonce,
    recover_x_partial_nonce_CVP,
    recover_x_partial_nonce_SVP
)
