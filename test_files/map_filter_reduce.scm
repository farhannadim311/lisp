(define (map f lst)
  (if (equal? lst ())                       ; empty list → done
      ()
      (cons (f (car lst))                   ; apply f to car
            (map f (cdr lst)))))            ; recurse on cdr

(define (filter f lst)
  (if (equal? lst ())
      ()                                        ; base case
      (if (f (car lst))                         ; keep the element?
          (cons (car lst)                       ; yes → put it in result
                (filter f (cdr lst)))           ;   and recurse
          (filter f (cdr lst)))))               ; no  → just recurse


(define (reduce f lst init)
  ;; Successively combine INIT with each element of LST from left to right.
  (if (equal? lst ())
      init                                  ; no more elements → result
      (reduce f                             ; recur with updated “so-far”
              (cdr lst)
              (f init (car lst)))))