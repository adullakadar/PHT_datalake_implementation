get 'pht_stock', 'DB1|PHT-01133'
get 'pht_stock', 'DB1|PHT-01133', {COLUMN => 's:qty', VERSIONS => 5}
scan 'pht_stock', {ROWPREFIXFILTER => 'AJM1|', LIMIT => 5}
scan 'pht_stock', {FILTER => "SingleColumnValueFilter('s', 'status', =, 'binary:REORDER')", LIMIT => 10}
exit
