# name required packages
list.of.packages <- c("ggplot2", "glue", "gt", "tidyverse", "webshot", "paletteer", "gtExtras")

# install required packages, if necessary, and load them ----
{
  new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[, "Package"])]
  if (length(new.packages)) install.packages(new.packages)
}

# Instead of using require, we'll use library to load the packages
lapply(list.of.packages, library, character.only = TRUE)

skipped <- read_csv('skipped_df.csv')

gap_table <- skipped %>%
  gt() %>% 
  tab_spanner(
    label = "The 7 large gaps in the logbooks",
    columns = c(logbook_dates, logbook_interval)
  ) %>% tab_spanner(
    label = "The 8 small gaps in the logbooks",
    columns = c(skipped_dates, skipped_interval)
  ) %>%
  cols_width(
    c(skipped_dates, logbook_dates) ~ px(300),
  )  %>%
  cols_label(
    logbook_dates = md("Dates of Identified Gap"),
    logbook_interval = "Duration of Gap",
    skipped_dates = md("Dates of Identified Gap"),
    skipped_interval = "Duration of Gap",
  )  %>% cols_align(
    align = "left", columns = c(skipped_dates, logbook_dates)
    )  %>% cols_align(
      align = "center", columns = c(skipped_interval, logbook_interval)
    ) %>% tab_header(
      title = md('Identified Logbook Gaps'),
      subtitle = md('Larger gaps on the left are included in our analyses, while smaller ones on the right are skipped.')
    ) %>% opt_table_font(
      font = list(
        google_font(name = "Garamond"),
        "Cochin", "Serif"
      ),
      weight= 'normal'
    )

gap_table %>%
  gtsave(
    glue::glue("gaps.png")
    # path = tempdir()
  ) 

updated_skipped <- read_csv('updated_skipped_df.csv')

updated_gap_table <- updated_skipped %>%
  gt() %>%
  cols_width(
    c(dates) ~ px(300),
  )  %>%
  cols_label(
    dates = md("Dates of Identified Gap"),
    interval = "Duration of Gap",
  ) %>%
  cols_hide(
    columns = c(
      status, start, end
    )
  ) %>% cols_align(
    align = "left", columns = c(dates)
  )  %>% cols_align(
    align = "center", columns = c(interval)
  ) %>% tab_header(
    title = md('All Identified Logbook Gaps'),
    subtitle = md('Longer included gaps are in bold, while shorter ones are skipped.')
  ) %>% opt_table_font(
    font = list(
      google_font(name = "Garamond"),
      "Cochin", "Serif"
    ),
    weight= 'normal'
  ) %>% tab_style(
    style = list(
      cell_text(weight = "bold")
    ),
    locations = cells_body(
      columns = c(interval, status),
      rows = (status == 'included')
    )
  )

updated_gap_table %>%
  gtsave(
    glue::glue("updated_gaps.png")
    # path = tempdir()
  ) 
