# src/tfg/recommendator/topsis.py
import numpy

def rank(matrix: list[list[float]], weights: list[float], is_benefit: list[bool]):
  X = numpy.array(matrix, dtype=float)
  norms = numpy.linalg.norm(X, axis=0)
  norms[norms == 0] = 1.0
  R = X / norms

  V = R * numpy.array(weights)

  benefit_mask = numpy.array(is_benefit)
  A_plus  = numpy.where(benefit_mask, V.max(axis=0), V.min(axis=0))
  A_minus = numpy.where(benefit_mask, V.min(axis=0), V.max(axis=0))

  s_plus  = numpy.linalg.norm(V - A_plus,  axis=1)
  s_minus = numpy.linalg.norm(V - A_minus, axis=1)

  denom = s_plus + s_minus
  denom[denom == 0] = 1e-12

  scores = s_minus / denom

  return scores.tolist()
