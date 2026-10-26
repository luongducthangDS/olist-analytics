// Power Query for the 4 tables in powerbi/. Create a Text parameter "Folder" = full path of powerbi\ (trailing \).
// One block = one query: New Source > Blank Query > Advanced Editor > paste > name it after the block.
// "en-US" in the type step: the CSVs use a decimal point and ISO dates. On a Vietnamese or European locale,
// 129.90 would otherwise load as 12990.

// ===== fact_orders
let
    Source = Csv.Document(File.Contents(Folder & "fact_orders.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Headers, {{"order_id", type text}, {"customer_unique_id", type text}, {"customer_state", type text}, {"seller_state", type text}, {"route", type text}, {"main_category", type text}, {"purchase_month", type date}, {"purchase_date", type date}, {"delivery_days", Int64.Type}, {"days_late", Int64.Type}, {"is_late", type logical}, {"items", Int64.Type}, {"items_value", type number}, {"freight_value", type number}, {"order_value", type number}, {"review_score", Int64.Type}}, "en-US")
in
    Typed

// ===== dim_state
let
    Source = Csv.Document(File.Contents(Folder & "dim_state.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Headers, {{"state", type text}, {"state_name", type text}, {"region", type text}}, "en-US")
in
    Typed

// ===== dim_category
let
    Source = Csv.Document(File.Contents(Folder & "dim_category.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Headers, {{"category", type text}}, "en-US")
in
    Typed

// ===== dim_date
let
    Source = Csv.Document(File.Contents(Folder & "dim_date.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Headers, {{"date", type date}, {"year", Int64.Type}, {"month", Int64.Type}, {"month_start", type date}}, "en-US")
in
    Typed
