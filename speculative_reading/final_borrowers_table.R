# name required packages
list.of.packages <- c("glue", "gt", "tidyverse", "webshot", "paletteer")

# install required packages, if necessary, and load them ----
{
  new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
  if(length(new.packages)) install.packages(new.packages)
  lapply(list.of.packages, require, character.only = TRUE)
}

df <- read_csv("final_top_results.csv")

names <- c('hemingway-ernest')

full_names <- c('Ernest Hemingway')


for (i in 1:length(names)){
  name <- names[i]
  full_name <- full_names[i]
  
  filtered_df <- df %>%
    filter(str_detect(member_period, name))
  
  
  gt_table <- filtered_df %>%
    mutate(blank_rowname = purrr::map(list(rep("&nbsp", 14)), gt::html)) %>%
    gt(
      #groupname_col = "period",
      rowname_col = "blank_rowname"
    ) %>%
    tab_row_group(
      label = "Subscription Period from March 28 1924 to March 28 1925",
      rows = period == "1924-03-28/1925-03-28"
    ) %>%
    tab_row_group(
      label = "Subscription Period from December 28 1921 to November 8 1922",
      rows = period == "1921-12-28/1922-11-08"
    ) %>%
    cols_hide(
      columns = c(
        member_period,
        member_id,
        period
      )
    ) %>%
    cols_width(
      c(lenskit_predicted_item, memory_cf_predicted_item) ~ px(300),
      c(`popular (all time)`, `popular (current)`) ~ px(200),
      c(lenskit_coef_variation, lenskit_median_score, memory_cf_coef_variation, memory_cf_median_score) ~ px(50),
      c( `popular scores (all time)`, `popular scores (current)`) ~ px(30),
    ) %>%
    fmt_percent(
      columns = c(lenskit_coef_variation, memory_cf_coef_variation)
    ) %>%
    fmt_markdown(
      columns = c(lenskit_predicted_item, memory_cf_predicted_item, `popular (all time)`, `popular (current)`)
    )%>%
    fmt_number(
      columns = c(lenskit_median_score, memory_cf_median_score),
      decimals = 3
    ) %>%
    cols_label(
      lenskit_predicted_item = md("Predicted Book by Implicit Matrix Factorization Model (IMF)"),
      lenskit_coef_variation=md("CV (IMF)"),
      lenskit_median_score=md("Score (IMF)"),
      memory_cf_predicted_item = md("Predicted Book by Memory-Based Collaborative Filtering (CF)"),
      memory_cf_coef_variation=md("CV (CF)"),
      memory_cf_median_score=md("Score (CF)"),
      `popular (all time)`=md("Most Popular Books<br>(1919-1942)"),
      `popular scores (all time)`=md("Total Borrows"),
      `popular (current)`=md("Most Popular Books<br>in Subscription Period"),
      `popular scores (current)`=md("Total Borrows"),
    ) %>%
    tab_style(
      locations = cells_row_groups(groups = everything()),
      style = list(
        cell_text(weight = "bold")
      )
    ) %>%
    tab_style(
      style = cell_fill(
        color = "#F0F8FF"
      ),
      locations = list(
        cells_body(
          columns = c(lenskit_coef_variation, memory_cf_coef_variation)
        ),
        cells_column_labels(
          columns = c(lenskit_coef_variation, memory_cf_coef_variation)
        )
      )
    ) %>%
    tab_style(
      style = cell_fill(
        color = "#F0F0F0"
      ),
      locations = list(
        cells_body(
          columns = c(lenskit_median_score, memory_cf_median_score, `popular scores (all time)`, `popular scores (current)`)
        ),
        cells_column_labels(
          columns = c(lenskit_median_score, memory_cf_median_score, `popular scores (all time)`, `popular scores (current)`)
        )
      )
    ) %>%
    cols_align(align = "center", columns = everything()) %>%
    # cols_align(align = "center", 
    #            columns = c(hinsage_predicted_item, lenskit_predicted_item, bipartite_predicted_item, `popular (all time)`, `popular scores (all time)`, `popular (current)`,`popular scores (current)`)) %>%
    # cols_align(align = "right", 
    #            columns = c(hinsage_median_score, hinsage_coef_variation, lenskit_median_score, lenskit_coef_variation, bipartite_median_score, bipartite_coef_variation)) %>%
    tab_header(
      title = 'Predicted Books for Ernest Hemingway',
      subtitle = "Predictions based on periods of known subscriptions with no extant borrowing records."
    )  %>%
    tab_footnote(
      footnote = "Score based on median of predictions from model or method.",
      locations = cells_column_labels(
        columns = c(lenskit_median_score, memory_cf_median_score)
      ) 
    ) %>%
    tab_footnote(
      footnote = "Ranked by coefficient of variation (CV) and then median scores (Score).",
      locations = cells_column_labels(
        columns = c(lenskit_predicted_item)
      )
    )
  # 
  gt_table
  
  gt_table %>%
    gtsave(
      glue::glue("{name}_table_predictions.png"),vwidth = 2000, vheight = 1000
      # path = tempdir()
    )
}

