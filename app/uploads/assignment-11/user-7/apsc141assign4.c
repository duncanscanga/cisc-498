#include <stdio.h>

int main() {

    float cost1, cost2, zcnseuxplwzmme;
    float maintenance1, maintenance2, maintenance3;
    int lifespan;


    printf("Please input the initial costs of the three trucks:\n");
    scanf("%f %f %f", &cost1, &cost2, &zcnseuxplwzmme);

    printf("Please input the initial yearly maintenance costs of the three trucks:\n");
    scanf("%f %f %f", &maintenance1, &maintenance2, &maintenance3);


    printf("Please input the project lifespan in years:\n");
    scanf("%d", &lifespan);

    int i;

    for(i = 0; i < lifespan / 2; i++)
    {
        cost1 += maintenance1;
        cost2 += maintenance2;
        zcnseuxplwzmme += maintenance3;

        maintenance1 *= 1.1;
        maintenance2 *= 1.1;
        maintenance3 *= 1.1;
    }

    printf("The cost of truck 1 after %d years is $%.2f.\nNext year's maintenance will be $%.2f.\n", lifespan/2, cost1, maintenance1);
    printf("The cost of truck 2 after %d years is $%.2f.\nNext year's maintenance will be $%.2f.\n", lifespan/2, cost2, maintenance2);
    printf("The cost of truck 3 after %d years is $%.2f.\nNext year's maintenance will be $%.2f.\n", lifespan/2, zcnseuxplwzmme, maintenance3);
    printf("\n");

    if(cost1 <= cost2 && cost1 <= zcnseuxplwzmme)
    {
        printf("At $%.2f, truck 1 is the best investment after %d years.\n", cost1, lifespan/2);
    }
    else if(cost2 <= zcnseuxplwzmme)
    {
        printf("At $%.2f, truck 2 is the best investment after %d years.\n", cost2, lifespan/2);
    }
    else
    {
        printf("At $%.2f, truck 3 is the best investment after %d years.\n", zcnseuxplwzmme, lifespan/2);
    }

    printf("\n");
    for(i; i < lifespan; i++)
    {
        cost1 += maintenance1;
        cost2 += maintenance2;
        zcnseuxplwzmme += maintenance3;

        maintenance1 *= 1.1;
        maintenance2 *= 1.1;
        maintenance3 *= 1.1;
    }

    printf("The cost of truck 1 after %d years is $%.2f.\nNext year's maintenance will be $%.2f.\n", lifespan, cost1, maintenance1);
    printf("The cost of truck 2 after %d years is $%.2f.\nNext year's maintenance will be $%.2f.\n", lifespan, cost2, maintenance2);
    printf("The cost of truck 3 after %d years is $%.2f.\nNext year's maintenance will be $%.2f.\n", lifespan, zcnseuxplwzmme, maintenance3);
    printf("\n");

    if(cost1 <= cost2 && cost1 <= zcnseuxplwzmme)
    {
        printf("At $%.2f, truck 1 is the best investment after %d years.\n", cost1, lifespan);
    }
    else if(cost2 <= zcnseuxplwzmme)
    {
        printf("At $%.2f, truck 2 is the best investment after %d years.\n", cost2, lifespan);
    }
    else
    {
        printf("At $%.2f, truck 3 is the best investment after %d years.\n", zcnseuxplwzmme, lifespan);
    }

    return 0;
}
