.new_result <- function(analysis, estimates, inputs = list()) {
  structure(list(analysis = analysis, estimates = estimates, inputs = inputs),
            class = c("jouriepi_analysis", "jouriepi_result", "list"))
}

#' @export
print.jouriepi_result <- function(x, ...) {
  cat("JouriEpi:", gsub("_", " ", x$analysis), "\n")
  print(as.data.frame(x, digits = 4L), row.names = FALSE, ...)
  invisible(x)
}

#' @export
summary.jouriepi_result <- function(object, ...) {
  structure(list(analysis = object$analysis, estimates = object$estimates,
                 inputs = object$inputs), class = "summary.jouriepi_result")
}

#' @export
print.summary.jouriepi_result <- function(x, ...) {
  cat("Summary - JouriEpi", gsub("_", " ", x$analysis), "\n")
  print(as.data.frame(.new_result(x$analysis, x$estimates, x$inputs), digits = 4L), row.names = FALSE, ...)
  invisible(x)
}

#' @export
print.jouriepi_data_health <- function(x, ...) {
  cat("JouriEpi data-health summary\n")
  cat("Rows received:", x$rows_received, " | returned:", x$rows_returned, "\n")
  cat("Exact duplicate rows removed:", x$exact_duplicate_rows_removed,
      " | duplicate-ID rows:", x$duplicate_id_rows, "\n")
  invisible(x)
}

#' @export
summary.jouriepi_data_health <- function(object, ...) object

#' @export
as.data.frame.jouriepi_data_health <- function(x, ...) {
  data.frame(metric = c("rows_received", "rows_returned", "exact_duplicate_rows_removed", "duplicate_id_rows"),
             value = c(x$rows_received, x$rows_returned, x$exact_duplicate_rows_removed, x$duplicate_id_rows))
}

#' @export
as.data.frame.jouriepi_result <- function(x, row.names = NULL, optional = FALSE, digits = 4L, ...) {
  if (length(digits) != 1L || !is.numeric(digits) || !is.finite(digits) ||
      digits < 0 || digits != as.integer(digits))
    stop("digits must be a nonnegative integer")
  format_number <- function(value, key) {
    if (is.na(value) || !is.finite(value)) return(as.character(value))
    if (grepl("(^|_)(p|p_value)$|p_value", key, ignore.case = TRUE) && value < 0.001)
      return("< 0.001")
    formatC(value, digits = digits, format = "f")
  }
  format_value <- function(value, key) {
    if (is.null(value) || length(value) == 0L) return(NA_character_)
    if (is.list(value) && !is.data.frame(value)) {
      parts <- vapply(seq_along(value), function(i) {
        nm <- names(value)[i]
        format_value(value[[i]], if (!is.null(nm) && nzchar(nm)) paste(key, nm, sep = "_") else key)
      }, character(1))
      return(paste(parts, collapse = ", "))
    }
    if (is.numeric(value)) {
      formatted <- vapply(value, format_number, character(1), key = key)
      separator <- if (grepl("ci|confidence_interval|confidence_limit", key, ignore.case = TRUE)) " to " else ", "
      return(paste(formatted, collapse = separator))
    }
    if (length(value) > 1L) return(paste(as.character(value), collapse = ", "))
    as.character(value)
  }
  if (is.data.frame(x$estimates)) {
    frame <- as.data.frame(x$estimates, row.names = row.names, ...)
    for (column in names(frame)) {
      if (is.numeric(frame[[column]])) {
        frame[[column]] <- vapply(frame[[column]], format_number, character(1), key = column)
      }
    }
    return(frame)
  }
  flatten <- function(value, prefix = "") {
    output <- list()
    if (is.list(value) && !is.data.frame(value)) {
      for (name in names(value)) {
        key <- if (nzchar(prefix)) paste(prefix, name, sep = ".") else name
        output <- c(output, flatten(value[[name]], key))
      }
    } else {
      output[[prefix]] <- format_value(value, prefix)
    }
    output
  }
  values <- flatten(x$estimates)
  data.frame(measure = names(values), estimate = unlist(values, use.names = FALSE),
             stringsAsFactors = FALSE, row.names = row.names)
}

#' @export
print.jouriepi_analysis <- function(x, ...) print.jouriepi_result(x, ...)
#' @export
summary.jouriepi_analysis <- function(object, ...) summary.jouriepi_result(object, ...)
#' @export
as.data.frame.jouriepi_analysis <- function(x, row.names = NULL, optional = FALSE, ...)
  as.data.frame.jouriepi_result(x, row.names=row.names, optional=optional, ...)

#' @export
as.data.frame.summary.jouriepi_result <- function(x, row.names=NULL, optional=FALSE, ...)
  as.data.frame.jouriepi_result(.new_result(x$analysis,x$estimates,x$inputs),
                                row.names=row.names,optional=optional,...)

to_latex <- function(x, ..., standalone = FALSE) {
  UseMethod("to_latex")
}

#' @export
to_latex.jouriepi_result <- function(x, caption = NULL, label = NULL, digits = 4L,
                                     ..., standalone = FALSE) {
  if (!is.logical(standalone) || length(standalone) != 1L || is.na(standalone))
    stop("standalone must be TRUE or FALSE")
  if (inherits(x,"summary.jouriepi_result")) x <- .new_result(x$analysis,x$estimates,x$inputs)
  if (!inherits(x, "jouriepi_result")) stop("x must be a jouriepi_result or its summary")
  if (length(digits) != 1L || !is.numeric(digits) || !is.finite(digits) || digits < 0 || digits != as.integer(digits))
    stop("digits must be a nonnegative integer")
  if (!is.null(caption) && (!is.character(caption) || length(caption)!=1L || is.na(caption))) stop("caption must be NULL or one character string")
  if (!is.null(label) && (!is.character(label) || length(label)!=1L || is.na(label))) stop("label must be NULL or one character string")
  frame <- as.data.frame(x, digits = digits)
  escape <- function(s) {
    s <- gsub("\\\\", "\\textbackslash{}", s)
    for (ch in c("&", "%", "$", "#", "_", "{", "}"))
      s <- gsub(ch, paste0("\\", ch), s, fixed=TRUE)
    s
  }
  values <- vapply(seq_len(nrow(frame)), function(i) {
    val <- frame$estimate[i]
    num <- suppressWarnings(as.numeric(val))
    if (!is.na(num) && is.finite(num)) formatC(num, digits=digits, format="f") else escape(val)
  }, character(1))
  row_end <- intToUtf8(c(92L, 92L))
  rows <- paste0(escape(frame$measure), " & ", values, " ", row_end)
  out <- c("\\begin{table}[ht]", "\\centering", "\\begin{tabular}{lr}",
           "\\toprule", paste0("Measure & Estimate ", row_end), "\\midrule", rows,
           "\\bottomrule", "\\end{tabular}")
  if (!is.null(caption)) out <- c(out, paste0("\\caption{", escape(caption), "}"))
  if (!is.null(label)) out <- c(out, paste0("\\label{", escape(label), "}"))
  fragment <- paste(c(out, "\\end{table}"), collapse="\n")
  if (!standalone) return(fragment)
  paste(c("\\documentclass{article}", "\\usepackage{booktabs}",
          "\\begin{document}", "", fragment, "", "\\end{document}"), collapse="\n")
}

#' @export
to_latex.summary.jouriepi_result <- function(x, caption = NULL, label = NULL,
                                             digits = 4L, ..., standalone = FALSE) {
  result <- .new_result(x$analysis, x$estimates, x$inputs)
  to_latex.jouriepi_result(result, caption = caption, label = label,
                           digits = digits, ..., standalone = standalone)
}
