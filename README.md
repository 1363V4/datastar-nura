no gif, video
sound ?
data...
count number of plays, pondère

ok découpler c'est dur parce que changer l'audio le coupe c'est normal 
js fixed it?
now playing focusable > done
data > mp3 done, 

découplage gif/mp3
tirage au sort
prefetch le suivant ?
delay avec rem
ne pas play si pas volume
idée:
faux element audio qu'on vient merge
on vient le changer et c'est sur lui qu'il y a le trigger
faut une route de plus ? faut stocker dans session ?


(cosmochess)
garder sa couleur (payant?)
filtrer gros mots
option pour garder l'input (clear par défaut)


ne pas se braquer
pas besoin de répéter

You can also change the behavior back to default when they stop playing.

The resource usage is more sending data when the user is not interacting and connection hanging around hogging server resources. So I'd probably have it as a separate connection than your view updates.
The defaults aggressive connection pruning makes a big difference for cpu/mem/network when you have a lot of concurrent users.
