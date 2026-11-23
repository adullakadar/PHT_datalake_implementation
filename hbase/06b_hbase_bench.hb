get 'pht_stock', 'DB1|PHT-01133'
put 'pht_stock', 'BENCH|PHT-01133', 's:qty', '25'
put 'pht_stock', 'BENCH|PHT-01133', 's:qty', '24'
put 'pht_stock', 'BENCH|PHT-01133', 's:qty', '20'
get 'pht_stock', 'BENCH|PHT-01133', {COLUMN => 's:qty', VERSIONS => 5}
deleteall 'pht_stock', 'BENCH|PHT-01133'
count 'pht_stock', INTERVAL => 20000, CACHE => 1000
exit
