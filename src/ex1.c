int square(int x) {
  return x*x;
}
int add(int x,int y) {
  return x+y;
}
int main() {
  int A[1000];
  int i,j,x;
  float f;

  j = 0.1;
  f = 0.1;

  do{
  j++;
  f = j + f;	
  } while (j != 2);

  for (i=0; i<1000; i++) A[i]=i;
  x=reduce(add,map(square,A));
  return x;
}