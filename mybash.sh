# my bash script
sudo python lab1.py
for i in 'seq 1:20'; do
curl -d 'entry=t'${i} -X 'POST' 'http://ip:80/10.1.0.1' &
echo "ciao"
done
