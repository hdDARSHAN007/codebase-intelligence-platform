
public class Calculator {
    private int total;

    public Calculator() {
        this.total = 0;
    }

    public int add(int a, int b) {
        return a + b;
    }

    interface Operation {
        int apply(int x, int y);
    }
}
