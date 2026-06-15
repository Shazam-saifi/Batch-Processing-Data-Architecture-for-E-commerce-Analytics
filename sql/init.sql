create schema if not exists analytics;

create table if not exists analytics.monthly_sales (
    sales_month date primary key,
    order_count integer not null,
    customer_count integer not null,
    item_count integer not null,
    gross_revenue numeric(12, 2) not null,
    avg_order_value numeric(12, 2) not null,
    loaded_at timestamp not null default current_timestamp
);

create table if not exists analytics.top_products (
    product_id integer primary key,
    product_name text not null,
    department text not null,
    order_count integer not null,
    total_quantity integer not null,
    gross_revenue numeric(12, 2) not null,
    reorder_rate numeric(6, 4) not null,
    loaded_at timestamp not null default current_timestamp
);

create table if not exists analytics.customer_metrics (
    user_id integer primary key,
    order_count integer not null,
    item_count integer not null,
    gross_revenue numeric(12, 2) not null,
    first_order_date date not null,
    last_order_date date not null,
    active_months integer not null,
    retention_flag boolean not null,
    loaded_at timestamp not null default current_timestamp
);

create table if not exists analytics.category_performance (
    department text primary key,
    order_count integer not null,
    product_count integer not null,
    item_count integer not null,
    gross_revenue numeric(12, 2) not null,
    loaded_at timestamp not null default current_timestamp
);

create table if not exists analytics.ml_customer_features (
    user_id integer primary key,
    order_count integer not null,
    item_count integer not null,
    gross_revenue numeric(12, 2) not null,
    avg_line_revenue numeric(12, 2) not null,
    avg_item_quantity numeric(12, 2) not null,
    reorder_rate numeric(6, 4) not null,
    department_count integer not null,
    active_months integer not null,
    last_order_date date not null,
    repeat_customer_label boolean not null,
    loaded_at timestamp not null default current_timestamp
);
